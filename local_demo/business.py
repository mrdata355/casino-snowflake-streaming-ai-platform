from __future__ import annotations

from decimal import Decimal


def net_gaming_revenue(
    gross_win: Decimal,
    adjustments: Decimal,
    voids: Decimal = Decimal("0"),
) -> Decimal:
    return gross_win - adjustments - voids


def location_profit(
    gaming_revenue: Decimal,
    pos_revenue: Decimal,
    labor_cost: Decimal,
    offer_cost: Decimal,
    other_direct_cost: Decimal = Decimal("0"),
) -> Decimal:
    return gaming_revenue + pos_revenue - labor_cost - offer_cost - other_direct_cost


def labor_cost_per_revenue_dollar(labor_cost: Decimal, net_revenue: Decimal) -> Decimal | None:
    if net_revenue == 0:
        return None
    return labor_cost / net_revenue
