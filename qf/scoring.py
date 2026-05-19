from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def zscore(s: pd.Series) -> pd.Series:
    x = s.astype(float)
    mu = x.mean(skipna=True)
    sd = x.std(skipna=True)
    if sd == 0 or np.isnan(sd):
        return x * 0.0
    return (x - mu) / sd


def score_cross_section(factors: pd.DataFrame, weights: Dict[str, float]) -> pd.Series:
    if factors.empty:
        return pd.Series(dtype=float)
    total = pd.Series(0.0, index=factors.index)
    for name, w in weights.items():
        if name not in factors.columns:
            continue
        zs = zscore(factors[name])
        total = total + float(w) * zs.fillna(0.0)
    return total

