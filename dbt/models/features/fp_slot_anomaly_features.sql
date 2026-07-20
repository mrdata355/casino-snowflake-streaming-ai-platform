{{ config(unique_key=['machine_id', 'feature_timestamp']) }}

select
    machine_id,
    property_id,
    window_start as feature_timestamp,
    coin_in,
    payout,
    jackpot_amount,
    fault_count,
    utilization_rate,
    avg(coin_in) over (
        partition by machine_id
        order by window_start
        rows between 11 preceding and current row
    ) as coin_in_60min_avg,
    stddev_samp(coin_in) over (
        partition by machine_id
        order by window_start
        rows between 11 preceding and current row
    ) as coin_in_60min_stddev,
    published_at as feature_created_at
from {{ ref('fact_slot_performance_5min') }}
