# Platform Components

The repository is organized as one integrated data platform with eight major capability areas.

## 1. Snowflake lakehouse foundation

Defines databases, schemas, warehouses, resource monitors, RBAC, masking policies, row-access policies, Time Travel settings, and validation views.

Primary paths:

```text
snowflake/
terraform/
```

## 2. Real-time event processing

Implements Kafka and Pub/Sub producers, Spark Structured Streaming, event-time processing, watermarks, deduplication, checkpoint recovery, dead-letter routing, and replay-safe Snowflake writes.

Primary paths:

```text
ingestion/
spark/
contracts/
```

## 3. Snowflake-native incremental processing

Uses Snowpipe, Snowpipe Streaming, Streams, Tasks, Dynamic Tables, and CDC patterns for workloads that remain within Snowflake.

Primary path:

```text
snowflake/
```

## 4. Revenue and profitability data products

Publishes certified slot performance, net gaming revenue, labor alignment, loyalty, attribution, and location profitability datasets.

Primary paths:

```text
dbt/models/gold/
dbt/models/silver/
dbt/tests/
```

## 5. Feature and scoring platform

Builds point-in-time training datasets, applies time-based validation, registers models with MLflow, publishes versioned model outputs, and monitors drift.

Primary paths:

```text
dbt/models/features/
ml/
services/feature_api/
```

## 6. Governed conversational analytics

Defines certified dimensions, metrics, synonyms, verified questions, role-aware access, and restrictions against exposing player-level PII.

Primary paths:

```text
snowflake/semantic/
services/cortex/
```

## 7. DataOps and infrastructure

Coordinates cross-system workflows, infrastructure provisioning, automated validation, environment promotion, and rollback procedures.

Primary paths:

```text
airflow/
.github/workflows/
terraform/
```

## 8. Contracts, governance, and observability

Defines schemas, ownership, reconciliation, freshness checks, cost attribution, security controls, incident response, replay, and recovery procedures.

Primary paths:

```text
contracts/
observability/
docs/runbook.md
docs/source_to_target.md
```

## Integration model

These capability areas operate as a single pipeline:

1. Source events and transactions enter through batch, CDC, Kafka, Pub/Sub, or Snowpipe Streaming.
2. Bronze preserves immutable source records and rejected payloads.
3. Silver standardizes, validates, deduplicates, and conforms entities.
4. Gold publishes governed business products.
5. Feature pipelines create point-in-time ML inputs.
6. Model pipelines register and publish versioned scores.
7. APIs and Cortex expose approved data products through governed interfaces.
8. Airflow, dbt, Terraform, CI, contracts, and observability enforce operational controls across the platform.
