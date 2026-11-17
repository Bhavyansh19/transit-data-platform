{{ config(alias='fct_realtime_departures') }}

select
    snapshot_hash,
    record_number,
    station_abbr,
    station_name,
    destination_abbr,
    destination_name,
    case
        when minutes ~ '^[0-9]+$' then minutes::integer
        else null
    end as minutes_until_departure,
    platform,
    direction,
    train_length,
    color,
    case
        when delay_seconds ~ '^[0-9]+$' then delay_seconds::integer
        else null
    end as delay_seconds,
    cancelled = '1' as is_cancelled,
    dynamic = '1' as is_dynamic,
    captured_at,
    source_file
from {{ ref('stg_realtime_etd') }}
