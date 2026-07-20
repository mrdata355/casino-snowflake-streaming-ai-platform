with silver as (
    select
        property_id,
        machine_id,
        time_slice(event_time, 5, 'MINUTE', 'START') as window_start,
        sum(net_gaming_revenue) as expected_revenue
    from {{ ref('silver_slot_events') }}
    group by 1, 2, 3
),
gold as (
    select property_id, machine_id, window_start, net_gaming_revenue
    from {{ ref('fact_slot_performance_5min') }}
)
select
    coalesce(s.property_id, g.property_id) as property_id,
    coalesce(s.machine_id, g.machine_id) as machine_id,
    coalesce(s.window_start, g.window_start) as window_start,
    s.expected_revenue,
    g.net_gaming_revenue
from silver s
full outer join gold g using (property_id, machine_id, window_start)
where abs(coalesce(s.expected_revenue, 0) - coalesce(g.net_gaming_revenue, 0)) > 0.01
