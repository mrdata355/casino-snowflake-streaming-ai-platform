# Production Architecture

## Primary design

The platform separates storage, compute, ownership, and consumption. Files and CDC enter Bronze through Snowpipe; high-frequency telemetry enters through Kafka or Pub/Sub and is processed by Spark Structured Streaming or Snowpipe Streaming. Snowflake Streams, Tasks, Dynamic Tables, and dbt publish conformed Silver entities, certified Gold products, semantic definitions, and point-in-time feature products.

## Reliability decisions

- Event IDs are globally unique and every sink is idempotent.
- Event time drives windows; ingestion time measures lateness and freshness.
- Watermarks bound streaming state while late-but-acceptable events are still processed.
- Invalid data is quarantined with the original payload and failure reason.
- Backfills use separate checkpoint paths and bounded date intervals.
- Gold publication is blocked when critical contracts or reconciliations fail.
- Workloads use isolated warehouses and query tags for performance and cost attribution.

## Data product contract

Every published product declares grain, primary and natural keys, source lineage, owner, freshness SLA, quality rules, PII classification, replay behavior, and recovery procedure. Dashboard, model, API, and Cortex consumers read certified interfaces rather than raw tables.
