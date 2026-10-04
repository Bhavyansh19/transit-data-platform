{{ config(alias='dim_service_calendar_dbt') }}

select *
from {{ ref('stg_service_calendar') }}
