-- First conceptual warehouse schema for TransitFlow.
-- This is documentation SQL for now; it is not connected to a database yet.

create table dim_stops (
    stop_id varchar primary key,
    stop_name varchar,
    stop_lat decimal(10, 7),
    stop_lon decimal(10, 7),
    parent_station varchar,
    platform_code varchar
);

create table dim_routes (
    route_id varchar primary key,
    route_short_name varchar,
    route_long_name varchar,
    route_color varchar
);

create table dim_trips (
    trip_id varchar primary key,
    route_id varchar,
    service_id varchar,
    trip_headsign varchar,
    direction_id integer
);

create table dim_service_calendar (
    service_id varchar primary key,
    monday integer,
    tuesday integer,
    wednesday integer,
    thursday integer,
    friday integer,
    saturday integer,
    sunday integer,
    start_date date,
    end_date date
);

create table fct_scheduled_stop_events (
    trip_id varchar,
    stop_sequence integer,
    stop_id varchar,
    route_id varchar,
    service_id varchar,
    arrival_time varchar,
    departure_time varchar,
    primary key (trip_id, stop_sequence),
    foreign key (stop_id) references dim_stops(stop_id),
    foreign key (route_id) references dim_routes(route_id),
    foreign key (trip_id) references dim_trips(trip_id),
    foreign key (service_id) references dim_service_calendar(service_id)
);
