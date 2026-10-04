select
    trip_id,
    stop_sequence,
    stop_id,
    route_id,
    service_id,
    arrival_time,
    departure_time
from {{ source('transitflow_warehouse', 'fct_scheduled_stop_events') }}
