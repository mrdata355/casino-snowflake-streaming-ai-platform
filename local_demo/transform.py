from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from local_demo.models import SlotEvent, SlotPerformanceWindow


def deduplicate_latest(events: list[SlotEvent]) -> list[SlotEvent]:
    latest: dict[str, SlotEvent] = {}
    for event in events:
        existing = latest.get(event.event_id)
        if existing is None or event.event_time >= existing.event_time:
            latest[event.event_id] = event
    return sorted(latest.values(), key=lambda event: (event.event_time, event.event_id))


def floor_to_five_minutes(value: datetime) -> datetime:
    return value.replace(minute=(value.minute // 5) * 5, second=0, microsecond=0)


def aggregate_slot_performance(events: list[SlotEvent]) -> list[SlotPerformanceWindow]:
    groups: dict[tuple[datetime, str, str, str], list[SlotEvent]] = defaultdict(list)
    for event in events:
        key = (
            floor_to_five_minutes(event.event_time),
            event.property_id,
            event.location_id,
            event.machine_id,
        )
        groups[key].append(event)

    output: list[SlotPerformanceWindow] = []
    for (window_start, property_id, location_id, machine_id), rows in sorted(groups.items()):
        sum_by_type = defaultdict(lambda: Decimal("0.00"))
        count_by_type: dict[str, int] = defaultdict(int)
        for row in rows:
            sum_by_type[row.event_type] += row.amount
            count_by_type[row.event_type] += 1

        output.append(
            SlotPerformanceWindow(
                window_start=window_start,
                window_end=window_start + timedelta(minutes=5),
                property_id=property_id,
                location_id=location_id,
                machine_id=machine_id,
                event_count=len(rows),
                spin_count=count_by_type["SPIN"],
                coin_in=sum_by_type["COIN_IN"],
                coin_out=sum_by_type["COIN_OUT"],
                jackpot_amount=sum_by_type["JACKPOT"],
                fault_count=count_by_type["FAULT"],
            )
        )
    return output
