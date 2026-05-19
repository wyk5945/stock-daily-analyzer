from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import akshare as ak


@dataclass(frozen=True)
class Stock:
    code: str
    name: str


class UniverseProvider:
    def get_universe(self, *, max_stocks: Optional[int] = None) -> List[Stock]:
        raise NotImplementedError


class AkshareAStockUniverseProvider(UniverseProvider):
    def __init__(self, *, exclude_prefix: List[str], include_prefix: Optional[List[str]] = None, exclude_st: bool = True):
        self._exclude_prefix = exclude_prefix
        self._include_prefix = include_prefix
        self._exclude_st = exclude_st

    def _valid_code(self, code: str) -> bool:
        c = str(code).split(".")[0]
        if self._include_prefix:
            ok = any(c.startswith(p) for p in self._include_prefix)
            if not ok:
                return False
        for p in self._exclude_prefix:
            if c.startswith(p):
                return False
        return True

    def get_universe(self, *, max_stocks: Optional[int] = None) -> List[Stock]:
        df = ak.stock_zh_a_spot_em()
        stocks: List[Stock] = []
        for _, row in df.iterrows():
            code = str(row.get("代码", "")).strip()
            name = str(row.get("名称", "")).strip()
            if not code:
                continue
            if not self._valid_code(code):
                continue
            if self._exclude_st and "ST" in name:
                continue
            stocks.append(Stock(code=code, name=name))
            if max_stocks and len(stocks) >= max_stocks:
                break
        return stocks
