{{ config(alias='fct_scheduled_stop_events_dbt') }}

select *
from {{ ref('stg_scheduled_stop_events') }}
