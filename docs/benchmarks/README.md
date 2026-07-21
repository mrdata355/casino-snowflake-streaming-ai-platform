# Scale Benchmarking

This benchmark harness validates the Snowflake portion of the platform at controlled data volumes without committing generated datasets to Git. It creates transient synthetic slot-event tables directly in Snowflake, applies data-quality filtering and replay-safe deduplication, publishes an hourly aggregate, records statement timings and validation results, then removes the benchmark tables unless retention is explicitly requested.

## Benchmark stages

Run the stages in order. Do not begin with the 1 TB stage.

| Stage | Logical payload | Purpose | Promotion gate |
|---|---:|---|---|
| Baseline | 10 GB | Validate SQL, permissions, query tags, cleanup, and report generation | Correct row counts, duplicates removed, invalid rows excluded, no unexpected spend |
| Tuning | 100 GB | Compare warehouse sizing, pruning, aggregation design, and runtime stability | Stable runtime, acceptable credit use, repeatable results |
| Scale | 1 TB | Produce the measured result used for the 10 TB projection | Successful completion, captured evidence, reconciled metrics, isolated warehouse |
| Projection | 10 TB | Estimate runtime and credits from the measured 1 TB run | Clearly labeled as a projection, not an executed workload |

The target is **logical random payload before Snowflake compression**. The actual compressed table size is captured from `SHOW TABLES` when available and will differ from the logical target.

## Safety controls

- Generated tables are `TRANSIENT` with zero-day Time Travel retention.
- The default run drops the raw and aggregate tables after metrics are captured.
- Execution requires the explicit `--confirm-scale-run` flag.
- Executable targets are restricted to 10 GB, 100 GB, and 1,000 GB.
- Every statement uses a query tag in the form `CASINO_SCALE_BENCHMARK:<RUN_ID>`.
- Use a dedicated benchmark warehouse with auto-suspend and a resource monitor.
- Do not run concurrent workloads on the benchmark warehouse when estimating credits.
- Do not commit generated SQL output, reports containing account identifiers, or data files.

## 1. Create a credential-free plan

```bash
python -m scripts.run_scale_benchmark plan \
  --target-gb 10 \
  --run-id scale_10gb_trial
```

The plan reports the target logical bytes and required generated row count. The default payload is 1,024 random characters per row.

## 2. Render SQL for review

```bash
python -m scripts.run_scale_benchmark render \
  --target-gb 10 \
  --run-id scale_10gb_trial \
  --database CASINO_DEV \
  --warehouse CASINO_DEV_TRANSFORM_WH \
  --out build/benchmarks/scale_10gb_trial.sql
```

Review the generated SQL before execution. Confirm the database, schema, warehouse, row count, query tag, transient-table configuration, and cleanup statements.

## 3. Execute the 10 GB baseline

Load the approved Snowflake credentials into the environment, isolate the warehouse, then run:

```bash
python -m scripts.run_scale_benchmark execute \
  --target-gb 10 \
  --run-id scale_10gb_trial \
  --database CASINO_DEV \
  --warehouse CASINO_DEV_TRANSFORM_WH \
  --project-to-tb 10 \
  --confirm-scale-run \
  --out build/benchmarks/scale_10gb_trial.json
```

`--credits-per-hour` must match the effective warehouse consumption rate for the warehouse used in the run. Omit it when uncertain; the report will leave credit projections blank rather than inventing a value.

By default, the benchmark drops its tables. Add `--retain-data` only when table inspection is required, and remove the tables immediately afterward.

## 4. Promote to 100 GB and 1 TB

After the 10 GB report is reviewed and accepted:

```bash
python -m scripts.run_scale_benchmark execute \
  --target-gb 100 \
  --run-id scale_100gb_tuning \
  --database CASINO_DEV \
  --warehouse CASINO_DEV_TRANSFORM_WH \
  --confirm-scale-run \
  --out build/benchmarks/scale_100gb_tuning.json
```

Only proceed to 1 TB after the 100 GB run is stable:

```bash
python -m scripts.run_scale_benchmark execute \
  --target-gb 1000 \
  --run-id scale_1tb_final \
  --database CASINO_DEV \
  --warehouse CASINO_DEV_TRANSFORM_WH \
  --project-to-tb 10 \
  --confirm-scale-run \
  --out build/benchmarks/scale_1tb_final.json
```

## Evidence to retain

Keep sanitized evidence, not generated data:

- Commit SHA and benchmark run ID
- Snowflake edition, region, warehouse name, size, and scaling policy
- Logical payload and generated row count
- Compressed table bytes from the captured `SHOW TABLES` result
- Runtime for generation, deduplication, aggregation, validation, and cleanup
- Raw rows, distinct event IDs, malformed rows, negative rows, and aggregate rows
- Warehouse isolation statement and resource-monitor configuration
- Credits or the exact method used to estimate them
- Query IDs and query-profile screenshots with account details removed
- Any failed run, root cause, corrective change, and rerun result

Use [report_template.md](report_template.md) to publish the final measured result. Never replace placeholders with estimated figures presented as measurements.

## Interpretation limits

The built-in 10 TB estimate is a linear projection. Real scaling can be nonlinear because of warehouse queuing, spill, clustering, compression, cloud-service overhead, concurrency, caching, and data distribution. The final report must distinguish:

- measured 1 TB values;
- calculated 10 TB projections;
- assumptions used in the calculation; and
- risks that could invalidate linear scaling.
