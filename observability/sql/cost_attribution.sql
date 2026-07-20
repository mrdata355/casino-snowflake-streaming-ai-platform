SELECT
    DATE_TRUNC('day', start_time) AS usage_day,
    warehouse_name,
    SUM(credits_used_compute) AS compute_credits,
    SUM(credits_used_cloud_services) AS cloud_services_credits
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 1 DESC, compute_credits DESC;

SELECT
    COALESCE(query_tag, 'UNTAGGED') AS query_tag,
    warehouse_name,
    COUNT(*) AS query_count,
    SUM(total_elapsed_time) / 1000 AS elapsed_seconds,
    SUM(bytes_scanned) AS bytes_scanned
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY bytes_scanned DESC;
