{{ config(alias='dim_trips_dbt') }}

select *
from {{ ref('stg_trips') }}
