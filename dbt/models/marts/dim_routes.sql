{{ config(alias='dim_routes_dbt') }}

select *
from {{ ref('stg_routes') }}
