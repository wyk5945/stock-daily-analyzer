from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


CASH = "__CASH__"


@dataclass
class TradeState:
    last_buy_date: Dict[str, pd.Timestamp]

    @classmethod
    def empty(cls) -> "TradeState":
        return cls(last_buy_date={})


@dataclass(frozen=True)
class TradingRules:
    t_plus_one: bool = True
    limit_up: float = 0.099
    limit_down: float = -0.099
    stamp_duty_bps: float = 10.0
    allow_buy_limit_up: bool = False
    allow_sell_limit_down: bool = False


def _get(df: pd.DataFrame, col: str, dt: pd.Timestamp) -> Optional[float]:
    if df is None or col not in df.columns:
        return None
    if dt not in df.index:
        return None
    try:
        v = float(df.loc[dt, col])
        if np.isnan(v):
            return None
        return v
    except Exception:
        return None


def _limit_flags(df: pd.DataFrame, prev_dt: pd.Timestamp, dt: pd.Timestamp, rules: TradingRules) -> Tuple[bool, bool]:
    c0 = _get(df, "Close", prev_dt)
    c1 = _get(df, "Close", dt)
    if c0 is None or c1 is None or c0 == 0:
        return False, False
    ret = c1 / c0 - 1.0
    return ret >= rules.limit_up, ret <= rules.limit_down


def _halted(df: pd.DataFrame, dt: pd.Timestamp) -> bool:
    v = _get(df, "Volume", dt)
    if v is None:
        return True
    return v <= 0


def ensure_cash(weights: Dict[str, float]) -> Dict[str, float]:
    w = dict(weights)
    w.pop(CASH, None)
    total = sum(max(0.0, float(v)) for v in w.values())
    cash = max(0.0, 1.0 - total)
    w[CASH] = cash
    s = sum(w.values())
    if s == 0:
        w[CASH] = 1.0
        return w
    if abs(s - 1.0) > 1e-9:
        w = {k: float(v) / s for k, v in w.items()}
    return w


def apply_constraints(
    *,
    panel: Dict[str, pd.DataFrame],
    prev_dt: pd.Timestamp,
    dt: pd.Timestamp,
    prev: Dict[str, float],
    target: Dict[str, float],
    rules: TradingRules,
    state: TradeState,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    prev_w = ensure_cash(prev)
    tgt_w = ensure_cash(target)

    eq_prev = {k: v for k, v in prev_w.items() if k != CASH}
    eq_tgt = {k: v for k, v in tgt_w.items() if k != CASH}

    executed = dict(eq_prev)

    for code, prev_weight in list(eq_prev.items()):
        target_weight = float(eq_tgt.get(code, 0.0))
        delta = target_weight - float(prev_weight)
        if delta >= 0:
            continue
        df = panel.get(code)
        if df is None or _halted(df, dt):
            continue
        limit_up, limit_down = _limit_flags(df, prev_dt, dt, rules)
        if limit_down and not rules.allow_sell_limit_down:
            continue
        if rules.t_plus_one and state.last_buy_date.get(code) == dt:
            continue
        executed[code] = float(prev_weight) + float(delta)

    executed_cash = 1.0 - sum(max(0.0, float(v)) for v in executed.values())
    executed_cash = max(0.0, executed_cash)

    desired_buys: Dict[str, float] = {}
    for code, target_weight in eq_tgt.items():
        prev_weight = float(eq_prev.get(code, 0.0))
        delta = float(target_weight) - prev_weight
        if delta <= 0:
            continue
        df = panel.get(code)
        if df is None or _halted(df, dt):
            continue
        limit_up, limit_down = _limit_flags(df, prev_dt, dt, rules)
        if limit_up and not rules.allow_buy_limit_up:
            continue
        desired_buys[code] = delta

    total_desired = sum(desired_buys.values())
    if total_desired > 0 and executed_cash > 0:
        scale = min(1.0, executed_cash / total_desired)
        for code, delta in desired_buys.items():
            executed[code] = float(executed.get(code, 0.0)) + float(delta) * scale

    next_w = ensure_cash({**executed, CASH: 0.0})

    buy_turnover: Dict[str, float] = {}
    sell_turnover: Dict[str, float] = {}
    for code in set(eq_prev.keys()) | set(next_w.keys()):
        if code == CASH:
            continue
        a = float(eq_prev.get(code, 0.0))
        b = float(next_w.get(code, 0.0))
        if b > a:
            buy_turnover[code] = b - a
        elif a > b:
            sell_turnover[code] = a - b

    for code, prev_weight in eq_prev.items():
        if float(next_w.get(code, 0.0)) > float(prev_weight):
            state.last_buy_date[code] = dt

    return next_w, {"buy": buy_turnover, "sell": sell_turnover}

