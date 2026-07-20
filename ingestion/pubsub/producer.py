from __future__ import annotations

import json
import os
from collections.abc import Iterable
from concurrent.futures import wait
from typing import Any

from google.cloud import pubsub_v1


def publish_events(events: Iterable[dict[str, Any]], topic_id: str | None = None) -> int:
    project_id = os.environ["GCP_PROJECT_ID"]
    resolved_topic = topic_id or os.getenv("PUBSUB_SLOT_TOPIC", "casino-slot-events-v1")
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, resolved_topic)
    futures = []

    for event in events:
        payload = json.dumps(event, separators=(",", ":")).encode("utf-8")
        futures.append(
            publisher.publish(
                topic_path,
                payload,
                event_id=str(event["event_id"]),
                machine_id=str(event["machine_id"]),
                schema_version=str(event.get("schema_version", "1")),
            )
        )

    wait(futures, timeout=30)
    failures = [future.exception() for future in futures if future.exception() is not None]
    if failures:
        raise RuntimeError(f"Pub/Sub publish failed for {len(failures)} events: {failures[0]}")
    return len(futures)
