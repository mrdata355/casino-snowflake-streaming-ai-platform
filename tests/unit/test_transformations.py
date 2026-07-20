from datetime import UTC, datetime
from decimal import Decimal

from local_demo.models import SlotEvent
from local_demo.transform import aggregate_slot_performance, deduplicate_latest


def _event(event_id: str, event_type: str, amount: str) -> SlotEvent:
    return SlotEvent(
        event_id=event_id,
        event_time=datetime(2026, 7, 20, 12, 1, tzinfo=UTC),
        property_id="P1",
        location_id="F1",
        machine_id="M1",
        event_type=event_type,
        amount=Decimal(amount),
    )


def test_deduplicate_and_aggregate() -> None:
    rows = [
        _event("e1", "COIN_IN", "100"),
        _event("e1", "COIN_IN", "100"),
        _event("e2", "COIN_OUT", "20"),
        _event("e3", "JACKPOT", "10"),
    ]
    clean = deduplicate_latest(rows)
    windows = aggregate_slot_performance(clean)

    assert len(clean) == 3
    assert len(windows) == 1
    assert windows[0].net_gaming_revenue == Decimal("70.00")
