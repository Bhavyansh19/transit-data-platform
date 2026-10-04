select
    route_id,
    route_short_name,
    route_long_name,
    route_color
from {{ source('transitflow_warehouse', 'dim_routes') }}
