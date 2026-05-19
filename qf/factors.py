from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd


def _close(df: pd.DataFrame) -> Optional[pd.Series]:
    for k in ["Close", "close"]:
        if k in df.columns:
            return df[k]
    return None


def _volume(df: pd.DataFrame) -> Optional[pd.Series]:
    for k in ["Volume", "volume"]:
        if k in df.columns:
            return df[k]
    return None


def rsi(close: pd.Series, period: int = 14) -> float:
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    v = 100 - (100 / (1 + rs))
    out = v.iloc[-1]
    return float(out) if out is not None and not np.isnan(out) else float("nan")


def momentum(close: pd.Series, lookback: int) -> float:
    if len(close) <= lookback:
        return float("nan")
    base = close.iloc[-lookback - 1]
    last = close.iloc[-1]
    if base == 0:
        return float("nan")
    return float((last - base) / base)


def volatility(close: pd.Series, lookback: int) -> float:
    if len(close) <= lookback:
        return float("nan")
    rets = close.pct_change().dropna().iloc[-lookback:]
    if rets.empty:
        return float("nan")
    return float(rets.std())


def volume_ratio(volume: pd.Series, window: int = 20) -> float:
    if len(volume) < window + 1:
        return float("nan")
    v = volume.iloc[-1]
    avg = volume.rolling(window=window).mean().iloc[-1]
    if avg == 0 or np.isnan(avg):
        return float("nan")
    return float(v / avg)


def compute_factor_snapshot(df: pd.DataFrame, *, lookback_days: int) -> Dict[str, float]:
    close = _close(df)
    vol = _volume(df)
    if close is None or close.empty:
        return {}

    out: Dict[str, float] = {
        "momentum": momentum(close, lookback_days),
        "volatility": volatility(close, lookback_days),
        "rsi": rsi(close, 14),
    }
    if vol is not None and not vol.empty:
        out["volume_ratio"] = volume_ratio(vol, 20)
    return out

