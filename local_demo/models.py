from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class SlotEvent:
    event_id: str
    event_time: datetime
    property_id: str
    location_id: str
    machine_id: str
    event_type: str
    amount: Decimal
    currency: str = "USD"
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["event_time"] = self.event_time.isoformat()
        row["amount"] = float(self.amount)
        return row


@dataclass(frozen=True, slots=True)
class SlotPerformanceWindow:
    window_start: datetime
    window_end: datetime
    property_id: str
    location_id: str
    machine_id: str
    event_count: int
    spin_count: int
    coin_in: Decimal
    coin_out: Decimal
    jackpot_amount: Decimal
    fault_count: int

    @property
    def net_gaming_revenue(self) -> Decimal:
        return self.coin_in - self.coin_out - self.jackpot_amount

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "property_id": self.property_id,
            "location_id": self.location_id,
            "machine_id": self.machine_id,
            "event_count": self.event_count,
            "spin_count": self.spin_count,
            "coin_in": float(self.coin_in),
            "coin_out": float(self.coin_out),
            "jackpot_amount": float(self.jackpot_amount),
            "fault_count": self.fault_count,
            "net_gaming_revenue": float(self.net_gaming_revenue),
        }
