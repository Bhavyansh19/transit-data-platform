# Local warehouse

TransitFlow uses a project-local PostgreSQL database for Week 4 practice.

The database runs on port `5433` and is named `transitflow`.

## Start the local database

From the project directory:

```bash
pg_ctl -D .postgres -o "-p 5433" -l .postgres/server.log start
```

## Load the schema and data

```bash
psql -p 5433 -d transitflow -f sql/warehouse_schema.sql
psql -p 5433 -d transitflow
```

The star-schema CSV files are loaded into:

- `dim_stops`
- `dim_routes`
- `dim_trips`
- `dim_service_calendar`
- `fct_scheduled_stop_events`

## Check the data

```sql
select count(*) from fct_scheduled_stop_events;

select
    r.route_short_name,
    count(*) as scheduled_stop_events
from fct_scheduled_stop_events f
left join dim_routes r
    on f.route_id = r.route_id
group by r.route_short_name
order by scheduled_stop_events desc;
```

The `.postgres/` directory is local database state and is intentionally not committed to Git.
