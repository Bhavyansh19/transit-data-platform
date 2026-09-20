-- Week 4/6: the fact table joining staged trip updates against dim_stations / dim_routes.
-- Remember: some Antioch/Pittsburg Center trip IDs won't match the static schedule directly —
-- this join needs reconciliation logic, not a naive equi-join.

select * from {{ ref('stg_trip_updates') }}
