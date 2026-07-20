{{ config(unique_key='event_id', cluster_by=['to_date(event_time)', 'property_id']) }}

with ranked as (
    select
        *,
        row_number() over (
            partition by event_id
            order by ingested_at desc
        ) as replay_rank
    from {{ ref('stg_slot_events') }}
    {% if is_incremental() %}
      where ingested_at >= (select dateadd('hour', -2, coalesce(max(ingested_at), '1970-01-01')) from {{ this }})
    {% endif %}
)
select
    event_id,
    machine_id,
    property_id,
    event_time,
    event_type,
    coin_in,
    payout,
    jackpot_amount,
    coin_in - payout - jackpot_amount as net_gaming_revenue,
    payload,
    ingested_at
from ranked
where replay_rank = 1
  and event_time <= dateadd('minute', 5, ingested_at)
  and coin_in >= 0
  and payout >= 0
