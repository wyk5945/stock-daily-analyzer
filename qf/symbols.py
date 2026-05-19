from __future__ import annotations


def to_yfinance_ticker(a_share_code: str) -> str:
    code = str(a_share_code).split(".")[0].strip()
    if code.startswith("6"):
        return f"{code}.SS"
    return f"{code}.SZ"

