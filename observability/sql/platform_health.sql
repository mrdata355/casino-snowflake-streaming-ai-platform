CREATE OR REPLACE VIEW ${DATABASE_NAME}.OPS.PLATFORM_HEALTH AS
WITH freshness AS (
    SELECT
        'slot_events_raw' AS component,
        DATEDIFF('minute', MAX(ingested_at), CURRENT_TIMESTAMP()) AS lag_minutes,
        IFF(lag_minutes <= 10, 'HEALTHY', IFF(lag_minutes <= 20, 'DEGRADED', 'CRITICAL')) AS status
    FROM ${DATABASE_NAME}.BRONZE.SLOT_EVENTS_RAW
),
quality AS (
    SELECT
        'critical_data_quality' AS component,
        COUNT_IF(status = 'FAIL' AND severity = 'CRITICAL') AS lag_minutes,
        IFF(lag_minutes = 0, 'HEALTHY', 'CRITICAL') AS status
    FROM ${DATABASE_NAME}.OPS.DQ_CHECK_RESULTS
    WHERE check_ts >= DATEADD('hour', -1, CURRENT_TIMESTAMP())
),
task_failures AS (
    SELECT
        'snowflake_tasks' AS component,
        COUNT_IF(state = 'FAILED') AS lag_minutes,
        IFF(lag_minutes = 0, 'HEALTHY', 'CRITICAL') AS status
    FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(SCHEDULED_TIME_RANGE_START=>DATEADD('hour', -1, CURRENT_TIMESTAMP())))
)
SELECT * FROM freshness
UNION ALL SELECT * FROM quality
UNION ALL SELECT * FROM task_failures;
