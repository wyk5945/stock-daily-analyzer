from pathlib import Path

from qf.config import load_experiment_config


def test_load_experiment_config():
    cfg = load_experiment_config(Path("experiments/default_a_share_daily.json"))
    assert cfg.market == "A股"
    assert cfg.frequency == "日频"
    assert cfg.backtest.rebalance in ("W-FRI", "W", "weekly")

