from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

from local_demo.models import SlotEvent

ALLOWED_EVENT_TYPES = {"SPIN", "COIN_IN", "COIN_OUT", "JACKPOT", "FAULT", "HEARTBEAT"}


@dataclass(frozen=True, slots=True)
class QualityResult:
    check_name: str
    status: str
    failed_count: int
    details: str


def validate_events(events: list[SlotEvent]) -> list[QualityResult]:
    ids = [event.event_id for event in events]
    duplicate_count = sum(count - 1 for count in Counter(ids).values() if count > 1)
    missing_key_count = sum(
        not all((event.event_id, event.property_id, event.machine_id, event.event_type)) for event in events
    )
    invalid_type_count = sum(event.event_type not in ALLOWED_EVENT_TYPES for event in events)
    negative_amount_count = sum(event.amount < Decimal("0") for event in events)

    return [
        _result("required_keys", missing_key_count, "Critical identifiers must be present"),
        _result("accepted_event_type", invalid_type_count, "Event type must be contract-approved"),
        _result("non_negative_amount", negative_amount_count, "Amounts cannot be negative"),
        _result("duplicate_event_id", duplicate_count, "Duplicates are expected to be deduplicated"),
    ]


def _result(name: str, failed_count: int, details: str) -> QualityResult:
    return QualityResult(
        check_name=name,
        status="PASS" if failed_count == 0 else "FAIL",
        failed_count=failed_count,
        details=details,
    )
