{{ config(alias='dim_stops_dbt') }}

select *
from {{ ref('stg_stops') }}
