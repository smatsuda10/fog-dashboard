{{ config(materialized='table') }}

-- ============================================================
-- Intermediate model: int_fog_features
-- Adds:
-- - is_foggy label
-- - lag features (1–24 hr)
-- - deltas
-- - 3-hr rolling averages
-- - time-based context
-- ============================================================

WITH base AS (

    SELECT
        *,
        -- Fog labeling rule
        CASE
            -- ✅ High-confidence: Any overcast layer with low ceiling
            WHEN (
                (sky_cover_1 = 'OVC' AND sky_altitude_1_ft IS NOT NULL AND sky_altitude_1_ft <= 1500)
                OR (sky_cover_2 = 'OVC' AND sky_altitude_2_ft IS NOT NULL AND sky_altitude_2_ft <= 1500)
                OR (sky_cover_3 = 'OVC' AND sky_altitude_3_ft IS NOT NULL AND sky_altitude_3_ft <= 1500)
            )
            THEN TRUE

            -- ✅ Sky data is missing, but strong fallback signal exists
            WHEN (
                sky_cover_1 = '<NA>'
            )
            AND (
                (visibility_km IS NOT NULL AND visibility_km <= 0.5)
                OR weather_codes = 'FG'
            )
            THEN TRUE

            -- ❌ Sky data missing and no fallback evidence — unclear
            WHEN (
                sky_cover_1 = '<NA>'
            )
            THEN NULL

            -- ✅ Sky data is present and shows no fog
            ELSE FALSE
        END AS is_foggy


    FROM {{ ref('staging_raw_hourly_data') }}

),

lagged AS (

    SELECT
        *,
        
        -- Lags
        LAG(temp_c, 1) OVER w AS temp_c_lag_1hr,
        LAG(dewpoint_c, 1) OVER w AS dewpoint_c_lag_1hr,
        LAG(humidity_percent, 1) OVER w AS humidity_lag_1hr,
        LAG(wind_speed_mps, 1) OVER w AS wind_speed_lag_1hr,
        LAG(visibility_km, 1) OVER w AS visibility_lag_1hr,

        LAG(temp_c, 2) OVER w AS temp_c_lag_2hr,
        LAG(temp_c, 3) OVER w AS temp_c_lag_3hr,
        LAG(temp_c, 12) OVER w AS temp_c_lag_12hr,
        LAG(temp_c, 24) OVER w AS temp_c_lag_24hr,

        LAG(humidity_percent, 2) OVER w AS humidity_lag_2hr,
        LAG(humidity_percent, 3) OVER w AS humidity_lag_3hr,
        LAG(humidity_percent, 12) OVER w AS humidity_lag_12hr,
        LAG(humidity_percent, 24) OVER w AS humidity_lag_24hr,

        LAG(visibility_km, 2) OVER w AS visibility_lag_2hr,
        LAG(visibility_km, 3) OVER w AS visibility_lag_3hr,
        LAG(visibility_km, 12) OVER w AS visibility_lag_12hr,
        LAG(visibility_km, 24) OVER w AS visibility_lag_24hr

    FROM base
    WINDOW w AS (PARTITION BY station_id ORDER BY timestamp_dt)

),

engineered AS (

    SELECT
        *,
        
        -- Delta features
        temp_c - temp_c_lag_1hr AS temp_delta_1hr,
        humidity_percent - humidity_lag_1hr AS humidity_delta_1hr,
        visibility_km - visibility_lag_1hr AS visibility_delta_1hr,

        -- Rolling 3-hour averages
        AVG(temp_c) OVER w3 AS temp_avg_3hr,
        AVG(humidity_percent) OVER w3 AS humidity_avg_3hr,
        AVG(visibility_km) OVER w3 AS visibility_avg_3hr,

        -- Local time-based context (corrected)
        CASE
            WHEN local_hour_of_day BETWEEN 0 AND 5 THEN TRUE
            ELSE FALSE
        END AS is_night,

        EXTRACT(MONTH FROM timestamp_local) AS month,

        CASE
            WHEN EXTRACT(MONTH FROM timestamp_local) IN (12, 1, 2) THEN 'winter'
            WHEN EXTRACT(MONTH FROM timestamp_local) IN (3, 4, 5) THEN 'spring'
            WHEN EXTRACT(MONTH FROM timestamp_local) IN (6, 7, 8) THEN 'summer'
            ELSE 'fall'
        END AS season

    FROM lagged
    WINDOW w3 AS (
        PARTITION BY station_id
        ORDER BY timestamp_dt
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    )

)

SELECT *
FROM engineered
ORDER BY station_id, timestamp_dt
