{{ config(materialized='table') }}



select *
from {{ source('fog_dashboard_project', 'hourly_weather_pacifica') }}

