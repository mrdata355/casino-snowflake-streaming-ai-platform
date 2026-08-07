from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from local_demo.models import SlotEvent

EVENT_TYPES = ("SPIN", "COIN_IN", "COIN_OUT", "JACKPOT", "FAULT", "HEARTBEAT")


def generate_slot_events(count: int, seed: int = 355) -> list[SlotEvent]:
    if count <= 0:
        raise ValueError("count must be positive")

    rng = random.Random(seed)
    base_time = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    events: list[SlotEvent] = []

    for index in range(count):
        event_type = rng.choices(
            EVENT_TYPES,
            weights=(38, 22, 20, 2, 3, 15),
            k=1,
        )[0]
        if event_type in {"FAULT", "HEARTBEAT", "SPIN"}:
            amount = Decimal("0.00")
        elif event_type == "JACKPOT":
            amount = Decimal(str(round(rng.uniform(500, 5000), 2)))
        else:
            amount = Decimal(str(round(rng.uniform(1, 150), 2)))

        events.append(
            SlotEvent(
                event_id=str(uuid.UUID(int=rng.getrandbits(128))),
                event_time=base_time + timedelta(seconds=index * 7),
                property_id="HR-FL-01",
                location_id=f"FLOOR-{index % 3 + 1}",
                machine_id=f"SLOT-{index % 25:04d}",
                event_type=event_type,
                amount=amount,
            )
        )

    # Include one deterministic duplicate for deduplication validation.
    if count >= 10:
        events.append(events[4])
    return events
