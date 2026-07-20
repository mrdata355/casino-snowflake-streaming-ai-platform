def test_net_gaming_revenue_formula():
    gross_win = 1000.0
    adjustments = 50.0
    assert gross_win - adjustments == 950.0


def test_location_profit_formula():
    gaming, pos, labor, offer = 1000.0, 250.0, 300.0, 100.0
    assert gaming + pos - labor - offer == 850.0
