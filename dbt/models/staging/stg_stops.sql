select
    stop_id,
    stop_name,
    stop_lat,
    stop_lon,
    parent_station,
    platform_code
from {{ source('transitflow_warehouse', 'dim_stops') }}
