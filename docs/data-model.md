# TransitFlow data model

This is the first warehouse model for TransitFlow.

## Grain

The main fact table has one row per scheduled trip at one stop sequence.

```text
one trip + one stop sequence = one fact row
```

## Star schema

```text
                 dim_stops
                     |
dim_routes — fct_scheduled_stop_events — dim_trips
                     |
              dim_service_calendar
```

## Fact table

### `fct_scheduled_stop_events`

One row represents one scheduled trip visiting one stop.

Important columns:

- `trip_id`
- `stop_id`
- `route_id`
- `service_id`
- `stop_sequence`
- `arrival_time`
- `departure_time`

The practical key is:

```text
trip_id + stop_sequence
```

This table stores events and schedule measurements.

## Dimension tables

### `dim_stops`

Describes stops and stations.

Source: `stops.txt`

Key: `stop_id`

Important attributes:

- `stop_name`
- `stop_lat`
- `stop_lon`
- `parent_station`
- `platform_code`

### `dim_routes`

Describes routes.

Source: `routes.txt`

Key: `route_id`

Important attributes:

- `route_short_name`
- `route_long_name`
- `route_color`

### `dim_trips`

Describes scheduled trips.

Source: `trips.txt`

Key: `trip_id`

Important attributes:

- `route_id`
- `service_id`
- `trip_headsign`
- `direction_id`

### `dim_service_calendar`

Describes when a trip normally operates.

Sources: `calendar.txt` and `calendar_dates.txt`

Key: `service_id`

## Why this design?

The fact table stores scheduled events. The dimension tables store descriptions of the things involved in those events.

This lets analysts query detailed events while still filtering by readable route, stop, trip, and service information.
