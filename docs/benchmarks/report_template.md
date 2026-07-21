# Snowflake Scale Benchmark Report

## Run identity

| Field | Value |
|---|---|
| Run ID | `<RUN_ID>` |
| Commit SHA | `<GIT_SHA>` |
| Execution date | `<UTC_TIMESTAMP>` |
| Engineer | Kellon Lewis |
| Snowflake region and edition | `<REDACTED_OR_SANITIZED_VALUE>` |
| Warehouse | `<WAREHOUSE_NAME_AND_SIZE>` |
| Query tag | `CASINO_SCALE_BENCHMARK:<RUN_ID>` |

## Scope

This run used synthetic casino slot-event data generated directly in Snowflake. The target volume represents logical random payload before compression. No production or customer data was used.

| Metric | Measured value |
|---|---:|
| Logical payload | `<GB_OR_TB>` |
| Generated rows | `<ROW_COUNT>` |
| Compressed raw-table bytes | `<BYTES>` |
| Aggregate rows | `<ROW_COUNT>` |
| Duplicate rows injected | `<COUNT>` |
| Malformed rows injected | `<COUNT>` |
| Negative-amount rows injected | `<COUNT>` |

## Configuration

- Warehouse size: `<SIZE>`
- Auto-suspend: `<SECONDS>`
- Multi-cluster setting: `<SETTING>`
- Resource monitor: `<MONITOR>`
- Concurrent workloads: `None` or `<DESCRIPTION>`
- Result cache state and handling: `<DESCRIPTION>`
- Data retention: `Transient tables, zero-day Time Travel`

## Measured results

| Operation | Runtime | Query ID | Rows affected | Bytes scanned or written |
|---|---:|---|---:|---:|
| Generate raw data | `<VALUE>` | `<QUERY_ID>` | `<VALUE>` | `<VALUE>` |
| Deduplicate and aggregate | `<VALUE>` | `<QUERY_ID>` | `<VALUE>` | `<VALUE>` |
| Validate results | `<VALUE>` | `<QUERY_ID>` | `<VALUE>` | `<VALUE>` |
| Cleanup | `<VALUE>` | `<QUERY_ID>` | `<VALUE>` | `<VALUE>` |

### Correctness checks

- Raw row count matches the generated plan: `<PASS_OR_FAIL>`
- Duplicate handling produced one surviving row per event ID: `<PASS_OR_FAIL>`
- Unsupported event types were excluded from the aggregate: `<PASS_OR_FAIL>`
- Negative amounts were excluded from the aggregate: `<PASS_OR_FAIL>`
- Revenue calculation reconciled to the accepted source rows: `<PASS_OR_FAIL>`
- Benchmark tables were removed after evidence collection: `<PASS_OR_FAIL>`

## Cost and throughput

| Metric | Measured value |
|---|---:|
| Total elapsed time | `<SECONDS>` |
| Logical throughput | `<GB_PER_MINUTE>` |
| Credits consumed or isolated estimate | `<CREDITS>` |
| Credits per logical TB | `<CREDITS_PER_TB>` |

Explain the credit source. State whether credits came from isolated warehouse metering or from elapsed time multiplied by the configured credits-per-hour rate.

## 10 TB projection

The projection below is calculated from the measured run and is not an executed 10 TB benchmark.

| Metric | Projection |
|---|---:|
| Source measured volume | `<MEASURED_TB>` |
| Target volume | `10 TB` |
| Projected elapsed time | `<VALUE>` |
| Projected credits | `<VALUE_OR_NOT_CALCULATED>` |

Formula:

```text
scale_factor = 10 TB / measured_TB
projected_runtime = measured_runtime * scale_factor
projected_credits = measured_credits * scale_factor
```

## Findings and engineering decisions

1. `<BOTTLENECK_OR_SUCCESS>`
2. `<WAREHOUSE_OR_SQL_TUNING_DECISION>`
3. `<DATA_QUALITY_OR_REPLAY_FINDING>`
4. `<COST_CONTROL_DECISION>`

## Limitations

Document caching, warehouse isolation, compression behavior, skew, spill, cloud-service overhead, and any reason the 10 TB projection might not scale linearly.

## Reproduction

```bash
<EXACT_SANITIZED_COMMAND>
```

Attach sanitized query-profile screenshots and the generated JSON report. Do not attach data files, credentials, account identifiers, or private key material.
