-- ============================================================
-- Future Plan Item 3: Conversion Lag Analysis
-- ============================================================
-- Distribution of time from impression to conversion, and from
-- last click to conversion.  Informs attribution window choice.
--
-- Time unit: seconds (confirmed in Block 2, max_day approx 30).
-- Input : stg_events view
-- Output: results/conversion_lag_buckets.csv
--         results/click_to_conv_lag.csv
-- ============================================================

-- Step 1: Impression-to-conversion lag distribution.
-- Reduce to one row per conversion: lag uses the last impression timestamp.
CREATE OR REPLACE TABLE res_conversion_lag AS
WITH conversion_level AS (
    SELECT
        conversion_id,
        MAX(conversion_ts) AS conversion_ts,
        MAX(ts) AS last_impression_ts
    FROM stg_events
    WHERE conversion_id IS NOT NULL
      AND conversion_id > 0
      AND conversion_ts IS NOT NULL
    GROUP BY conversion_id
), lags AS (
    SELECT conversion_id, conversion_ts - last_impression_ts AS lag_seconds
    FROM conversion_level
    WHERE conversion_ts >= last_impression_ts
)
SELECT
    CASE
        WHEN lag_seconds <=          3600 THEN '1. le1h'
        WHEN lag_seconds <=         86400 THEN '2. 1h-1d'
        WHEN lag_seconds <=     3 * 86400 THEN '3. 1d-3d'
        WHEN lag_seconds <=     7 * 86400 THEN '4. 3d-7d'
        WHEN lag_seconds <=    14 * 86400 THEN '5. 7d-14d'
        WHEN lag_seconds <=    30 * 86400 THEN '6. 14d-30d'
        ELSE                                   '7. gt30d'
    END                                AS lag_bucket,
    COUNT(*)                           AS conversions,
    ROUND(AVG(lag_seconds) / 3600, 2)  AS avg_lag_hours,
    ROUND(MIN(lag_seconds) / 3600, 2)  AS min_lag_hours,
    ROUND(MAX(lag_seconds) / 3600, 2)  AS max_lag_hours
FROM lags
GROUP BY 1
ORDER BY 1;

COPY res_conversion_lag TO 'results/conversion_lag_buckets.csv' (HEADER, DELIMITER ',');

-- Step 2: Click-to-conversion lag.
-- Reduce click lag to one row per conversion using its last clicked impression.
CREATE OR REPLACE TABLE res_click_to_conv_lag AS
WITH click_lags AS (
    SELECT
        conversion_id,
        (MAX(conversion_ts) - MAX(CASE WHEN click = 1 THEN ts END)) / 3600.0
            AS hours_since_last_click
    FROM stg_events
    WHERE conversion_id IS NOT NULL
      AND conversion_id > 0
      AND conversion_ts IS NOT NULL
    GROUP BY conversion_id
    HAVING MAX(CASE WHEN click = 1 THEN ts END) IS NOT NULL
       AND MAX(conversion_ts) > MAX(CASE WHEN click = 1 THEN ts END)
)
SELECT
    CASE
        WHEN hours_since_last_click <=   1 THEN '1. le1h'
        WHEN hours_since_last_click <=  24 THEN '2. 1h-24h'
        WHEN hours_since_last_click <=  72 THEN '3. 1d-3d'
        WHEN hours_since_last_click <= 168 THEN '4. 3d-7d'
        ELSE                                    '5. gt7d'
    END                                AS click_lag_bucket,
    COUNT(DISTINCT conversion_id)      AS conversions
FROM click_lags
GROUP BY 1
ORDER BY 1;

COPY res_click_to_conv_lag TO 'results/click_to_conv_lag.csv' (HEADER, DELIMITER ',');

-- Step 3: Percentile summary for the memo.
SELECT
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY lag_seconds) / 3600.0, 2) AS p25_hours,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY lag_seconds) / 3600.0, 2) AS p50_hours,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY lag_seconds) / 3600.0, 2) AS p75_hours,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY lag_seconds) / 3600.0, 2) AS p90_hours,
    COUNT(*) AS total_conversions
FROM (
    SELECT conversion_id, MAX(conversion_ts) - MAX(ts) AS lag_seconds
    FROM stg_events
    WHERE conversion_id IS NOT NULL
      AND conversion_id > 0
      AND conversion_ts IS NOT NULL
    GROUP BY conversion_id
    HAVING MAX(conversion_ts) >= MAX(ts)
) conversion_lags;
