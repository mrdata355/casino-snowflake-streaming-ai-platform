# Topic 1 — Snowflake Production Foundation

## Objective
Design and implement a repeatable DEV, QA, and PROD Snowflake foundation with least-privilege RBAC, isolated compute, cost controls, deterministic grants, and safe rollback.

## Business context
The casino platform must support batch ingestion, near-real-time telemetry, governed transformation, ML feature engineering, Cortex consumption, and production operations without allowing one workload to exhaust compute or expose sensitive player data.

## Learning sequence
1. Define environment and object naming standards.
2. Design the role hierarchy.
3. Create workload-isolated warehouses.
4. Create databases and managed-access schemas.
5. Apply ownership and future grants.
6. Add resource monitors and query controls.
7. Validate positive and negative access paths.
8. document deployment, cloning, rollback, and recovery.

## Architecture decision
Use one database per environment and a consistent schema topology inside each database.

| Environment | Database | Purpose |
|---|---|---|
| DEV | `CASINO_DEV` | Engineering development and destructive testing |
| QA | `CASINO_QA` | Integration, reconciliation, performance, and release validation |
| PROD | `CASINO_PROD` | Governed production workloads |

Each database contains:

- `BRONZE` — source-aligned raw records, JSON payloads, CDC metadata, offsets, filenames, and load audit columns.
- `SILVER` — validated, deduplicated, standardized, and conformed enterprise entities.
- `GOLD` — certified casino-domain data products and stable business grains.
- `SEMANTIC` — governed metrics, secure views, semantic definitions, and verified conversational queries.
- `FEATURES` — point-in-time feature products, labels, and governed scoring outputs.
- `OPS` — run logs, data-quality results, contract results, watermarks, incidents, and audit records.
- `TEMP` — explicitly nonproduction scratch objects with retention controls.

## Workload isolation

| Warehouse | Workload | Initial size | Auto-suspend target |
|---|---|---:|---:|
| `WH_INGEST_<ENV>` | Snowpipe follow-up, copy, CDC landing, ingestion validation | XSMALL | 60 seconds |
| `WH_TRANSFORM_<ENV>` | dbt, Streams/Tasks, Dynamic Tables, Silver/Gold transformation | SMALL | 120 seconds |
| `WH_FEATURE_<ENV>` | feature generation, training-set assembly, batch scoring | SMALL | 120 seconds |
| `WH_CORTEX_<ENV>` | semantic and conversational consumption | XSMALL | 60 seconds |
| `WH_ADMIN_<ENV>` | controlled deployment and validation only | XSMALL | 60 seconds |

Production sizing begins conservatively and is changed only from measured queue time, spill, latency, concurrency, and cost evidence.

## RBAC design

### System roles
- `ACCOUNTADMIN`: break-glass account administration only.
- `SECURITYADMIN`: role and grant administration.
- `SYSADMIN`: infrastructure and object ownership delegation.

### Platform roles
- `RL_PLATFORM_ADMIN`: owns environment databases and warehouses through controlled deployment.
- `RL_SECURITY_ADMIN`: owns managed-access grant decisions.
- `RL_DATA_ENGINEER`: engineering access to approved nonproduction objects and production operational views.
- `RL_DATA_SCIENTIST`: read access to approved Gold and Features products; write access only to governed experiment or output schemas.
- `RL_ANALYST`: read access to approved Gold and Semantic objects.
- `RL_OPERATIONS`: operational monitoring, task inspection, controlled reruns, and incident response.

### Service roles
- `SRV_INGEST_<ENV>`: stage, pipe, raw-table, and ingestion-metadata privileges only.
- `SRV_TRANSFORM_<ENV>`: read Bronze, write Silver/Gold, execute approved tasks, and use transform warehouse.
- `SRV_FEATURE_<ENV>`: read approved Silver/Gold, write Features, and use feature warehouse.
- `SRV_CORTEX_<ENV>`: read only approved Semantic and governed feature/Gold views; no raw-player-table access.
- `SRV_ORCHESTRATOR_<ENV>`: execute approved procedures/tasks and inspect operational metadata without broad table ownership.

Human users receive functional roles. Machines receive service roles. Runtime services never use `ACCOUNTADMIN`.

## Variable register
Fill these before executing any DDL.

| Variable | Example | Your value |
|---|---|---|
| `ORG_NAME` | `MRDATA_LABS` | |
| `PLATFORM_PREFIX` | `CASINO` | |
| `ENVIRONMENT` | `DEV` | |
| `DATABASE_NAME` | `CASINO_DEV` | |
| `ADMIN_USER` | `KELLON_LEWIS` | |
| `ALERT_USER` | `KELLON_LEWIS` | |
| `INGEST_CREDIT_QUOTA` | `20` | |
| `TRANSFORM_CREDIT_QUOTA` | `40` | |
| `FEATURE_CREDIT_QUOTA` | `30` | |
| `CORTEX_CREDIT_QUOTA` | `20` | |
| `DATA_RETENTION_DAYS_DEV` | `1` | |
| `DATA_RETENTION_DAYS_QA` | `3` | |
| `DATA_RETENTION_DAYS_PROD` | `7` | |

## Naming standard

```text
Database:       CASINO_<ENV>
Schema:         <LAYER>
Warehouse:      WH_<WORKLOAD>_<ENV>
Resource monitor: RM_<WORKLOAD>_<ENV>
Functional role: RL_<FUNCTION>
Service role:    SRV_<SERVICE>_<ENV>
Task:            TSK_<DOMAIN>_<ACTION>
Stream:          STR_<SOURCE>_<OBJECT>
Dynamic table:   DT_<DOMAIN>_<GRAIN>
```

## Implementation files

```text
snowflake/ddl/00_bootstrap.sql
snowflake/ddl/01_roles.sql
snowflake/ddl/02_resource_monitors.sql
snowflake/ddl/03_warehouses.sql
snowflake/ddl/04_databases_schemas.sql
snowflake/ddl/05_grants.sql
snowflake/tests/test_access_controls.sql
snowflake/tests/test_cost_controls.sql
terraform/modules/snowflake_foundation/
terraform/environments/dev.tfvars
terraform/environments/qa.tfvars
terraform/environments/prod.tfvars
docs/runbooks/snowflake_environment_recovery.md
```

## Physical coding assessment — Part 1
Without copying the final implementation, write SQL that:

1. Creates `CASINO_DEV`.
2. Creates all seven schemas.
3. Creates `WH_INGEST_DEV` and `WH_TRANSFORM_DEV`.
4. Enables auto-resume and conservative auto-suspend.
5. Creates separate resource monitors for ingestion and transformation.
6. Sends a notification before quota exhaustion.
7. Suspends at quota and suspends immediately beyond quota.
8. Creates one human engineering role and two service roles.
9. Ensures the ingestion service can write Bronze but cannot write Silver.
10. Ensures the transformation service can read Bronze and write Silver/Gold.

## Required explanation
Be ready to answer:

- Why isolate compute by workload instead of sharing one warehouse?
- Why should object ownership and data access be separated?
- Why use managed-access schemas?
- Why are future grants useful, and what risk do they introduce if designed carelessly?
- Why should a service role not inherit a broad human role?
- How would you prove a forbidden operation actually fails?
- How would you promote the same topology from DEV to QA and PROD?

## Definition of done
- All objects are reproducible from code.
- No runtime identity uses a system administrator role.
- Positive and negative access tests are executable.
- Warehouses have auto-suspend, statement timeouts, and resource monitors.
- DEV, QA, and PROD use the same module with different values.
- Production changes require a pull request and an approved deployment path.
- Recovery steps identify the last good commit, clone/restore option, validation queries, and decision owner.
