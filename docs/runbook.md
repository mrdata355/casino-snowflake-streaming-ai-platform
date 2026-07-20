# Production Runbook

## Triage order

1. Confirm business impact, affected products, incident start time, and severity.
2. Check source freshness, Kafka/Pub/Sub lag, Spark query progress, Snowflake task history, dbt results, and publication gates.
3. Identify the last successful event offset, batch ID, watermark, model version, and Git SHA.
4. Stop unsafe publication while preserving raw ingestion whenever possible.

## Replay procedure

- Create a bounded replay interval and unique checkpoint path.
- Read immutable Bronze data or broker offsets from the last verified position.
- Write through the same deterministic event keys and MERGE logic.
- Reconcile source counts, distinct keys, revenue totals, and rejected records.
- Reopen publication only after critical tests pass.

## Rollback procedure

- Suspend dependent Snowflake tasks.
- Restore changed tables using zero-copy clone or Time Travel into a recovery schema.
- Revert the deployment commit or promote the last approved dbt state.
- Validate object grants, row counts, business metrics, and consumer access.
- Resume tasks in dependency order and record the incident timeline.

## Never do

Never delete checkpoints to force a restart, manually edit production totals, expose rejected PII in logs, or rerun an unbounded interval without reconciliation and approval.
