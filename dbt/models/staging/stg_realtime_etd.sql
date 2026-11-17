select
    snapshot_hash,
    record_number,
    station_abbr,
    station_name,
    destination_abbr,
    destination_name,
    minutes,
    platform,
    direction,
    train_length,
    color,
    delay_seconds,
    cancelled,
    dynamic,
    captured_at,
    source_file
from {{ source('transitflow_warehouse', 'fct_realtime_etd') }}
