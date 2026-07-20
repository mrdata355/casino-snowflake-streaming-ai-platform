#!/usr/bin/env bash
set -euo pipefail

BROKER="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
CONTAINER="${KAFKA_CONTAINER_NAME:-casino-snowflake-streaming-ai-platform-kafka-1}"
TOPICS=(
  "${KAFKA_SLOT_TOPIC:-casino.slot.events.v1}:12:3"
  "${KAFKA_TABLE_TOPIC:-casino.table.events.v1}:6:3"
  "${KAFKA_SLOT_DLQ_TOPIC:-casino.slot.events.dlq.v1}:3:3"
)

for specification in "${TOPICS[@]}"; do
  IFS=: read -r topic partitions replication <<<"$specification"
  docker exec "$CONTAINER" /opt/bitnami/kafka/bin/kafka-topics.sh \
    --bootstrap-server "$BROKER" \
    --create --if-not-exists \
    --topic "$topic" \
    --partitions "$partitions" \
    --replication-factor "${KAFKA_REPLICATION_FACTOR:-1}"
done

docker exec "$CONTAINER" /opt/bitnami/kafka/bin/kafka-topics.sh \
  --bootstrap-server "$BROKER" --list
