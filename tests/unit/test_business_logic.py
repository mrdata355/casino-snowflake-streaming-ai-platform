from decimal import Decimal

from local_demo.business import (
    labor_cost_per_revenue_dollar,
    location_profit,
    net_gaming_revenue,
)


def test_net_gaming_revenue() -> None:
    assert net_gaming_revenue(Decimal("1000"), Decimal("50"), Decimal("10")) == Decimal("940")


def test_location_profit_prevents_fact_fanout_formula_error() -> None:
    result = location_profit(
        gaming_revenue=Decimal("1000"),
        pos_revenue=Decimal("250"),
        labor_cost=Decimal("300"),
        offer_cost=Decimal("100"),
    )
    assert result == Decimal("850")


def test_labor_ratio_handles_zero_revenue() -> None:
    assert labor_cost_per_revenue_dollar(Decimal("100"), Decimal("0")) is None
