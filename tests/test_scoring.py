import pandas as pd

from qf.scoring import score_cross_section


def test_score_cross_section_runs():
    df = pd.DataFrame(
        {
            "momentum": [0.1, 0.2, 0.0],
            "volatility": [0.03, 0.01, 0.02],
        },
        index=["a", "b", "c"],
    )
    s = score_cross_section(df, {"momentum": 1.0, "volatility": -0.5})
    assert list(s.index) == ["a", "b", "c"]

