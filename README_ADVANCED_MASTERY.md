# OpsReady Advanced Mastery V3

The Production Control Room now includes seven additional graded workbenches beyond the live incident simulator and 30-defect repair bay.

## Advanced workbenches

- **SQL Patterns — 14 scenarios**: anti-joins, deterministic dedupe, Top-N, running totals, rolling windows, month-over-month growth, FULL OUTER reconciliation, SCD2 as-of joins, Snowflake FLATTEN, idempotent MERGE, incremental watermarks, pruning-safe filters, gaps-and-islands/sessionization, and conditional control totals.
- **PySpark Transformations — 12 scenarios**: explicit schemas, nested explode, deterministic Window dedupe, streaming watermark/dedupe, distributed aggregations, left-anti joins, conditional quality classification, safe broadcast, repartition/AQE reasoning, foreachBatch MERGE, rolling windows, and corrupt-JSON quarantine.
- **Python Unit Testing — 8 scenarios**: pytest parameterization, DataFrame equality, HTTP timeout mocking, 429 retry behavior, idempotency regression, breaking-schema validation, control-total invariants, and scoring API contract tests.
- **dbt Development — 8 scenarios**: staging contracts, incremental models with lookback, generic tests, source freshness, singular reconciliation tests, safe-divide macros, SCD2 snapshots, and semantic metric governance.
- **API + Scoring — 8 scenarios**: FastAPI/Pydantic contracts, scoring provenance, bounded retries/timeouts, cursor pagination, idempotent mutations, batch scoring, least-privilege analytics, and SLO instrumentation.
- **Development & CI/CD — 8 scenarios**: pre-merge gates, secret handling, canaries, rollback/data-acceptance separation, feature flags, bounded migrations/backfills, post-deploy observability, and production Definition of Done.
- **Incident Triage — 8 scenarios**: reward duplication, credential exposure, Kafka skew, scoring latency, dbt documentation failures, ML drift/capacity, worker recovery, and post-deploy reconciliation failures.

## Scoring model

Each code lab evaluates required production patterns and explicitly penalizes known anti-patterns when applicable. Best scores persist locally by scenario. The Control Room emits lab evidence into OpsReady so Manager View can display recorded attempts and scores.

The advanced labs are intentionally **simulated execution environments**, not arbitrary code execution sandboxes. They train code shape, production reasoning, safety, failure modes, and acceptance criteria while remaining safe for a static Vercel demo.
