from qf.portfolio import build_equal_weight_portfolio


def test_equal_weight_with_cap():
    sel = ["a", "b", "c", "d", "e", "f", "g", "h"]
    p = build_equal_weight_portfolio(sel, max_weight_per_name=0.15)
    assert abs(sum(p.weights.values()) - 1.0) < 1e-9
    assert max(p.weights.values()) <= 0.15 + 1e-9

