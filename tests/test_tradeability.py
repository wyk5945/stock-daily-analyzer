import pandas as pd

from qf.trading import TradingRules, TradeState, CASH, apply_constraints, ensure_cash


def test_limit_up_blocks_buy():
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    df = pd.DataFrame({"Close": [100.0, 110.0], "Volume": [1000.0, 1000.0]}, index=dates)
    panel = {"000001": df}

    prev = ensure_cash({CASH: 1.0})
    target = ensure_cash({"000001": 1.0})

    next_w, turns = apply_constraints(
        panel=panel,
        prev_dt=dates[0],
        dt=dates[1],
        prev=prev,
        target=target,
        rules=TradingRules(limit_up=0.099, allow_buy_limit_up=False),
        state=TradeState.empty(),
    )
    assert next_w.get("000001", 0.0) == 0.0
    assert next_w[CASH] == 1.0

