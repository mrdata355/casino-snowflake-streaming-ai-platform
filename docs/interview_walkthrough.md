# Five-Minute Interview Walkthrough

## Minute 1: Business objective

Explain that the platform produces trusted casino revenue, slot utilization, player value, labor efficiency, profitability, ML features, and governed conversational analytics from synthetic transactional and streaming data.

## Minute 2: Streaming path

Show the event contract, Kafka/Pub/Sub producer, Spark schema enforcement, watermark, deduplication, DLQ, checkpoint, and replay-safe Snowflake MERGE. State the exact event grain and latency target.

## Minute 3: Snowflake-native path

Show Snowpipe, Streams, Tasks, Dynamic Tables, RBAC, resource monitors, Time Travel, query tags, and isolated warehouses. Explain where dbt is used and where native Snowflake orchestration is preferable.

## Minute 4: AI/ML consumption

Show point-in-time features, time-based train/test split, MLflow registration, model output contract, PSI drift monitoring, semantic definitions, verified Cortex questions, and role-aware API access.

## Minute 5: Operations

Show CI, Terraform, publication gates, reconciliation tests, cost queries, incident runbook, rollback, and GitHub history. Be explicit that the project is a production-style reference implementation using synthetic data, not a deployed Hard Rock system.
