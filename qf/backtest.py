from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd

from qf.data import PriceProvider
from qf.factors import compute_factor_snapshot
from qf.metrics import compute_metrics, PerfMetrics
from qf.portfolio import build_equal_weight_portfolio, select_top_k
from qf.scoring import score_cross_section
from qf.trading import TradingRules, TradeState, CASH, apply_constraints, ensure_cash
from qf.universe import Stock


def _parse_date(s: str) -> pd.Timestamp:
    return pd.to_datetime(s).normalize()


def _rebalance_dates(dates: pd.DatetimeIndex, rule: str) -> pd.DatetimeIndex:
    s = pd.Series(index=dates, data=1.0)
    if rule in ("W", "W-FRI", "weekly"):
        return s.resample("W-FRI").last().dropna().index
    if rule == "M":
        return s.resample("M").last().dropna().index
    return s.resample("W-FRI").last().dropna().index


@dataclass(frozen=True)
class BacktestResult:
    equity: pd.Series
    daily_returns: pd.Series
    holdings: pd.DataFrame
    metrics: PerfMetrics


class DailyBacktester:
    def __init__(
        self,
        *,
        price_provider: PriceProvider,
        timeout_seconds: int,
        lookback_days: int,
        factor_weights: Dict[str, float],
        top_k: int,
        max_weight_per_name: float,
        commission_bps: float,
        slippage_bps: float,
        trading_rules: TradingRules,
        max_drawdown_halt: Optional[float],
    ):
        self._prices = price_provider
        self._timeout = timeout_seconds
        self._lookback = lookback_days
        self._factor_weights = factor_weights
        self._top_k = top_k
        self._max_w = max_weight_per_name
        self._commission_bps = commission_bps
        self._slippage_bps = slippage_bps
        self._rules = trading_rules
        self._mdd_halt = max_drawdown_halt

    def _load_panel(self, universe: List[Stock], *, start: str, end: str) -> Dict[str, pd.DataFrame]:
        panel: Dict[str, pd.DataFrame] = {}
        for s in universe:
            pf = self._prices.history(s.code, start=start, end=end, timeout_seconds=self._timeout)
            if pf is None:
                continue
            df = pf.df
            if "Close" not in df.columns:
                continue
            df = df.copy()
            df.index = pd.to_datetime(df.index).normalize()
            panel[s.code] = df
        return panel

    def run(self, universe: List[Stock], *, start: str, end: str, rebalance: str, initial_cash: float) -> BacktestResult:
        start_ts = _parse_date(start)
        end_ts = _parse_date(end)
        panel = self._load_panel(universe, start=start, end=end)
        if not panel:
            equity = pd.Series(dtype=float)
            return BacktestResult(equity=equity, daily_returns=equity, holdings=pd.DataFrame(), metrics=compute_metrics(equity))

        all_dates = sorted({d for df in panel.values() for d in df.index})
        dates = pd.DatetimeIndex([d for d in all_dates if start_ts <= d <= end_ts]).sort_values()
        if dates.empty:
            equity = pd.Series(dtype=float)
            return BacktestResult(equity=equity, daily_returns=equity, holdings=pd.DataFrame(), metrics=compute_metrics(equity))

        rebal_dates = set(_rebalance_dates(dates, rebalance))

        holdings: Dict[str, float] = {CASH: 1.0}
        holdings = ensure_cash(holdings)
        state = TradeState.empty()
        equity_curve: List[Tuple[pd.Timestamp, float]] = []
        holdings_rows: List[Dict[str, float]] = []
        halted = False

        equity = initial_cash
        equity_peak = initial_cash

        dt0 = dates[0]
        equity_curve.append((dt0, equity))
        holdings_rows.append({"Date": dt0, **holdings})

        for i in range(1, len(dates)):
            dt = dates[i]
            prev_dt = dates[i - 1]
            if halted:
                equity_curve.append((dt, equity))
                holdings_rows.append({"Date": dt, **holdings})
                continue

            day_ret = 0.0
            for code, w in holdings.items():
                if code == CASH:
                    continue
                df = panel.get(code)
                if df is None:
                    continue
                if prev_dt not in df.index or dt not in df.index:
                    continue
                c0 = float(df.loc[prev_dt, "Close"])
                c1 = float(df.loc[dt, "Close"])
                if c0 == 0:
                    continue
                day_ret += w * ((c1 - c0) / c0)

            equity = equity * (1.0 + day_ret)
            equity_peak = max(equity_peak, equity)
            if self._mdd_halt is not None:
                dd = equity / equity_peak - 1.0
                if dd <= -abs(float(self._mdd_halt)):
                    holdings = {CASH: 1.0}
                    holdings = ensure_cash(holdings)
                    halted = True

            if dt in rebal_dates and not halted:
                factors_rows: Dict[str, Dict[str, float]] = {}
                for code, df in panel.items():
                    hist = df[df.index <= dt].tail(self._lookback + 30)
                    if len(hist) < self._lookback + 2:
                        continue
                    snap = compute_factor_snapshot(hist, lookback_days=self._lookback)
                    if snap:
                        factors_rows[code] = snap
                if factors_rows:
                    factors_df = pd.DataFrame.from_dict(factors_rows, orient="index")
                    scores = score_cross_section(factors_df, self._factor_weights)
                    selected = select_top_k(scores, top_k=self._top_k)
                    target_eq = build_equal_weight_portfolio(selected, max_weight_per_name=self._max_w).weights
                    target = ensure_cash(target_eq)
                else:
                    target = ensure_cash({})

                next_holdings, turns = apply_constraints(
                    panel=panel,
                    prev_dt=prev_dt,
                    dt=dt,
                    prev=holdings,
                    target=target,
                    rules=self._rules,
                    state=state,
                )

                buy_turn = sum(turns["buy"].values())
                sell_turn = sum(turns["sell"].values())
                cost_rate = (self._commission_bps + self._slippage_bps) / 10_000.0
                stamp_rate = self._rules.stamp_duty_bps / 10_000.0
                cost = equity * ((buy_turn + sell_turn) * cost_rate + sell_turn * stamp_rate)
                equity = equity - cost
                holdings = next_holdings

            equity_curve.append((dt, equity))
            holdings_rows.append({"Date": dt, **holdings})

        equity_series = pd.Series({d: v for d, v in equity_curve}).sort_index()
        daily_returns = equity_series.pct_change().fillna(0.0)
        holdings_df = pd.DataFrame(holdings_rows).set_index("Date").fillna(0.0)
        metrics = compute_metrics(equity_series)
        return BacktestResult(equity=equity_series, daily_returns=daily_returns, holdings=holdings_df, metrics=metrics)
