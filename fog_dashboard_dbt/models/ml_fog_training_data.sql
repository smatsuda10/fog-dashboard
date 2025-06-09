{{ config(materialized='table') }}

-- 1. Get is_foggy values from ~6:30 PM to 8:00 PM local time
WITH fog_window AS (
    SELECT
        local_date,
        station_id,
        COUNTIF(is_foggy IS NOT NULL) AS total_valid_points,
        SUM(CASE WHEN is_foggy = TRUE THEN 1 ELSE 0 END) AS foggy_points
    FROM {{ ref('int_fog_features') }}
    WHERE 
      (local_hour_of_day = 18 AND EXTRACT(MINUTE FROM timestamp_local) >= 30)
      OR local_hour_of_day = 19
      OR (local_hour_of_day = 20 AND EXTRACT(MINUTE FROM timestamp_local) <= 59)
    GROUP BY local_date, station_id
),

-- 2. Create a label: TRUE if >= 70% of points in the window were foggy
fog_labels AS (
    SELECT
        local_date,
        station_id,
        SAFE_DIVIDE(foggy_points, total_valid_points) AS fog_fraction,
        SAFE_DIVIDE(foggy_points, total_valid_points) >= 0.70 AS is_foggy_at_7pm
    FROM fog_window
),

-- 3. Select the closest row to 7 PM per day/station with non-null core features
ranked_candidates AS (
    SELECT
        *,
        ABS(local_hour_of_day - 19) AS hour_diff,
        ROW_NUMBER() OVER (
            PARTITION BY local_date, station_id
            ORDER BY ABS(local_hour_of_day - 19), timestamp_dt
        ) AS rownum
    FROM {{ ref('int_fog_features') }}
    WHERE 
      (
        (local_hour_of_day = 18 AND EXTRACT(MINUTE FROM timestamp_local) >= 30)
        OR local_hour_of_day = 19
        OR (local_hour_of_day = 20 AND EXTRACT(MINUTE FROM timestamp_local) <= 59)
      )
      AND temp_c IS NOT NULL
      AND humidity_percent IS NOT NULL
      AND visibility_km IS NOT NULL
),

features_at_7pm AS (
    SELECT
        local_date,
        station_id,
        temp_c,
        dewpoint_c,
        humidity_percent,
        wind_speed_mps,
        wind_direction_deg,
        visibility_km,
        altimeter_inhg,
        precip_1hr_in,
        temp_c_lag_1hr,
        humidity_lag_1hr,
        visibility_lag_1hr,
        temp_delta_1hr,
        humidity_delta_1hr,
        visibility_delta_1hr,
        temp_avg_3hr,
        humidity_avg_3hr,
        visibility_avg_3hr,
        is_night,
        season,
        EXTRACT(MONTH FROM local_date) AS month
    FROM ranked_candidates
    WHERE rownum = 1
),

-- 4. Bring in yesterday’s 7 PM features + fog label
yesterday_7pm AS (
    SELECT
        local_date AS local_date_plus1,
        station_id,
        temp_c AS temp_c_7pm_yesterday,
        dewpoint_c AS dewpoint_c_7pm_yesterday,
        humidity_percent AS humidity_7pm_yesterday,
        visibility_km AS visibility_7pm_yesterday,
        is_foggy_at_7pm AS is_foggy_at_7pm_yesterday
    FROM {{ this }}
    WHERE is_foggy_at_7pm IS NOT NULL
),

-- 5. Identify fallback cases with no valid 7PM-ish data
fallbacks AS (
    SELECT
        local_date,
        station_id,
        COUNT(*) AS total_points,
        COUNTIF(temp_c IS NOT NULL AND humidity_percent IS NOT NULL AND visibility_km IS NOT NULL) AS valid_points
    FROM {{ ref('int_fog_features') }}
    WHERE 
      (local_hour_of_day = 18 AND EXTRACT(MINUTE FROM timestamp_local) >= 30)
      OR local_hour_of_day = 19
      OR (local_hour_of_day = 20 AND EXTRACT(MINUTE FROM timestamp_local) <= 59)
    GROUP BY local_date, station_id
    HAVING valid_points = 0
)

-- 6. Join today's 7 PM features + today's fog label + yesterday context
SELECT
    f.*,
    l.is_foggy_at_7pm,
    l.fog_fraction,
    y.temp_c_7pm_yesterday,
    y.dewpoint_c_7pm_yesterday,
    y.humidity_7pm_yesterday,
    y.visibility_7pm_yesterday,
    y.is_foggy_at_7pm_yesterday
FROM features_at_7pm f
LEFT JOIN fog_labels l
  ON f.local_date = l.local_date
 AND f.station_id = l.station_id
LEFT JOIN yesterday_7pm y
  ON DATE_SUB(f.local_date, INTERVAL 1 DAY) = y.local_date_plus1
 AND f.station_id = y.station_id
LEFT JOIN fallbacks b
  ON f.local_date = b.local_date
 AND f.station_id = b.station_id
WHERE b.local_date IS NULL
ORDER BY f.local_date, f.station_id
