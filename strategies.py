from typing import Dict, List

import numpy as np

from config import MAX_RECOMMENDATIONS_PER_TYPE, MIN_VOLUME_RATIO, RSI_OVERSOLD_SCREEN


class Strategy:
    name: str = ""

    def select(self, stocks: List[Dict]) -> List[Dict]:
        raise NotImplementedError


class OversoldReboundStrategy(Strategy):
    name = "超卖反弹"

    def select(self, stocks: List[Dict]) -> List[Dict]:
        candidates = [
            s
            for s in stocks
            if s["rsi"] < RSI_OVERSOLD_SCREEN and s["macd_bullish"] and not np.isnan(s["rsi"])
        ]
        candidates.sort(key=lambda x: x["rsi"])
        return candidates[:MAX_RECOMMENDATIONS_PER_TYPE]


class TrendingUpStrategy(Strategy):
    name = "趋势向好"

    def select(self, stocks: List[Dict]) -> List[Dict]:
        candidates = [
            s
            for s in stocks
            if s["ma_bullish"] and s["macd_bullish"] and 40 < s["rsi"] < 70 and not np.isnan(s["rsi"])
        ]
        candidates.sort(key=lambda x: x["weekly_change"], reverse=True)
        return candidates[:MAX_RECOMMENDATIONS_PER_TYPE]


class VolumeBreakoutStrategy(Strategy):
    name = "放量突破"

    def select(self, stocks: List[Dict]) -> List[Dict]:
        candidates = [
            s
            for s in stocks
            if s["vol_ratio"] > MIN_VOLUME_RATIO
            and s["daily_change"] > 0.01
            and s["rsi"] < 75
            and not np.isnan(s["rsi"])
        ]
        candidates.sort(key=lambda x: x["daily_change"], reverse=True)
        return candidates[:MAX_RECOMMENDATIONS_PER_TYPE]


def default_strategies() -> List[Strategy]:
    return [OversoldReboundStrategy(), TrendingUpStrategy(), VolumeBreakoutStrategy()]

