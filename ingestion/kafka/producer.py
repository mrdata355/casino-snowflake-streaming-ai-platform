from __future__ import annotations

import json
import os
from collections.abc import Iterable
from typing import Any

from confluent_kafka import Producer


def build_producer() -> Producer:
    config: dict[str, Any] = {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "enable.idempotence": True,
        "acks": "all",
        "compression.type": "snappy",
        "linger.ms": 20,
        "batch.num.messages": 1000,
        "client.id": "casino-slot-event-producer",
    }
    security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
    config["security.protocol"] = security_protocol
    if security_protocol.startswith("SASL"):
        config.update(
            {
                "sasl.mechanism": os.environ["KAFKA_SASL_MECHANISM"],
                "sasl.username": os.environ["KAFKA_SASL_USERNAME"],
                "sasl.password": os.environ["KAFKA_SASL_PASSWORD"],
            }
        )
    return Producer(config)


def publish_events(events: Iterable[dict[str, Any]], topic: str | None = None) -> int:
    producer = build_producer()
    target_topic = topic or os.getenv("KAFKA_SLOT_TOPIC", "casino.slot.events.v1")
    delivered = 0

    def delivery_report(error: Exception | None, message: Any) -> None:
        nonlocal delivered
        if error is not None:
            raise RuntimeError(f"Kafka delivery failed: {error}")
        delivered += 1

    for event in events:
        event_id = str(event["event_id"])
        producer.produce(
            target_topic,
            key=event_id.encode("utf-8"),
            value=json.dumps(event, separators=(",", ":")).encode("utf-8"),
            on_delivery=delivery_report,
        )
        producer.poll(0)

    remaining = producer.flush(30)
    if remaining:
        raise TimeoutError(f"{remaining} Kafka messages were not delivered")
    return delivered
