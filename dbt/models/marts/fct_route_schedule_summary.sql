{{ config(alias='fct_route_schedule_summary') }}

select
    events.route_id,
    routes.route_short_name,
    count(*) as scheduled_stop_events,
    count(distinct events.trip_id) as scheduled_trips,
    count(distinct events.stop_id) as scheduled_stops
from {{ ref('stg_scheduled_stop_events') }} as events
left join {{ ref('stg_routes') }} as routes
    on events.route_id = routes.route_id
group by
    events.route_id,
    routes.route_short_name
