{{ config(materialized='table') }}

WITH source_data AS (

    SELECT
        station_id,
        timestamp,
        SAFE_CAST(longitude AS FLOAT64) AS longitude,
        SAFE_CAST(latitude AS FLOAT64) AS latitude,
        SAFE_CAST(temp_f AS FLOAT64) AS temp_f,
        SAFE_CAST(dewpoint_f AS FLOAT64) AS dewpoint_f,
        SAFE_CAST(humidity_percent AS FLOAT64) AS humidity_percent,
        SAFE_CAST(wind_direction_deg AS FLOAT64) AS wind_direction_deg,
        SAFE_CAST(wind_speed_kt AS FLOAT64) AS wind_speed_kt,
        SAFE_CAST(precip_1hr_in AS FLOAT64) AS precip_1hr_in,
        SAFE_CAST(altimeter_inhg AS FLOAT64) AS altimeter_inhg,
        SAFE_CAST(visibility_miles AS FLOAT64) AS visibility_miles,
        SAFE_CAST(wind_gust_kt AS FLOAT64) AS wind_gust_kt,
        sky_cover_1,
        sky_cover_2,
        sky_cover_3,
        SAFE_CAST(sky_altitude_1_ft AS INT64) AS sky_altitude_1_ft,
        SAFE_CAST(sky_altitude_2_ft AS INT64) AS sky_altitude_2_ft,
        SAFE_CAST(sky_altitude_3_ft AS INT64) AS sky_altitude_3_ft,
        weather_codes

    FROM {{ source('fog_dashboard_project', 'hourly_weather_pacifica') }}

),

transformed AS (

    SELECT
        *,
        
        -- UTC time fields
        DATETIME(timestamp) AS timestamp_dt,
        EXTRACT(DATE FROM timestamp) AS date,
        EXTRACT(HOUR FROM timestamp) AS hour_of_day,
        EXTRACT(DAYOFWEEK FROM timestamp) AS day_of_week,

        -- Local time conversion (Pacific Time)
        DATETIME(TIMESTAMP(timestamp), "America/Los_Angeles") AS timestamp_local,
        EXTRACT(DATE FROM DATETIME(TIMESTAMP(timestamp), "America/Los_Angeles")) AS local_date,
        EXTRACT(HOUR FROM DATETIME(TIMESTAMP(timestamp), "America/Los_Angeles")) AS local_hour_of_day,
        EXTRACT(DAYOFWEEK FROM DATETIME(TIMESTAMP(timestamp), "America/Los_Angeles")) AS local_day_of_week,

        -- Unit conversions
        SAFE_DIVIDE(wind_speed_kt, 1.94384) AS wind_speed_mps,
        SAFE_DIVIDE(wind_gust_kt, 1.94384) AS wind_gust_mps,
        SAFE_DIVIDE((temp_f - 32) * 5, 9) AS temp_c,
        SAFE_DIVIDE((dewpoint_f - 32) * 5, 9) AS dewpoint_c,
        SAFE_MULTIPLY(visibility_miles, 1.60934) AS visibility_km

    FROM source_data

)

SELECT *
FROM transformed
ORDER BY station_id, timestamp_dt
