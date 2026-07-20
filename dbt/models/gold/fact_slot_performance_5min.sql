{{ config(unique_key=['machine_id', 'window_start']) }}

with events as (
    select *
    from {{ ref('silver_slot_events') }}
    {% if is_incremental() %}
      where event_time >= (select dateadd('hour', -2, coalesce(max(window_start), '1970-01-01')) from {{ this }})
    {% endif %}
),
aggregated as (
    select
        property_id,
        machine_id,
        time_slice(event_time, 5, 'MINUTE', 'START') as window_start,
        count(*) as event_count,
        count_if(event_type = 'PLAY') as play_count,
        count_if(event_type = 'FAULT') as fault_count,
        sum(coin_in) as coin_in,
        sum(payout) as payout,
        sum(jackpot_amount) as jackpot_amount,
        sum(net_gaming_revenue) as net_gaming_revenue,
        max(ingested_at) as latest_ingested_at
    from events
    group by 1, 2, 3
)
select
    *,
    iff(event_count = 0, 0, play_count / event_count::float) as utilization_rate,
    current_timestamp() as published_at
from aggregated
