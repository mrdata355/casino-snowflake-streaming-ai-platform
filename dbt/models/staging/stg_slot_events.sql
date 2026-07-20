with source as (
    select * from {{ source('bronze', 'slot_events_raw') }}
),
renamed as (
    select
        event_id::varchar as event_id,
        machine_id::varchar as machine_id,
        property_id::varchar as property_id,
        event_time::timestamp_ntz as event_time,
        upper(event_type::varchar) as event_type,
        coalesce(coin_in, 0)::number(18,2) as coin_in,
        coalesce(payout, 0)::number(18,2) as payout,
        coalesce(jackpot_amount, 0)::number(18,2) as jackpot_amount,
        payload,
        ingested_at::timestamp_ntz as ingested_at
    from source
)
select * from renamed
