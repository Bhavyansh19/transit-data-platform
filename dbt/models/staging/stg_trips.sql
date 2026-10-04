select
    trip_id,
    route_id,
    service_id,
    trip_headsign,
    direction_id
from {{ source('transitflow_warehouse', 'dim_trips') }}
