select
    snapshot_hash,
    entity_id,
    trip_id,
    captured_at,
    source_file
from {{ source('transitflow_warehouse', 'fct_realtime_trip_updates') }}
