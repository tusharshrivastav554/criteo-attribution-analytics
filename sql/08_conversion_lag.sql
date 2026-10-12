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
CREATE OR REPLACE TABLE res_conversion_lag AS
WITH lags AS (
    SELECT
        conversion_id,
        campaign,
        click,
        (conversion_ts - ts) AS lag_seconds
    FROM stg_events
    WHERE conversion_id IS NOT NULL
      AND conversion_ts IS NOT NULL
      AND (conversion_ts - ts) >= 0
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
    COUNT(DISTINCT conversion_id)      AS conversions,
    COUNT(*)                           AS touchpoints,
    ROUND(AVG(lag_seconds) / 3600, 2)  AS avg_lag_hours,
    ROUND(MIN(lag_seconds) / 3600, 2)  AS min_lag_hours,
    ROUND(MAX(lag_seconds) / 3600, 2)  AS max_lag_hours
FROM lags
GROUP BY 1
ORDER BY 1;

COPY res_conversion_lag TO 'results/conversion_lag_buckets.csv' (HEADER, DELIMITER ',');

-- Step 2: Click-to-conversion lag.
-- time_since_last_click is pre-nullified in stg_events.
CREATE OR REPLACE TABLE res_click_to_conv_lag AS
WITH click_lags AS (
    SELECT DISTINCT
        conversion_id,
        time_since_last_click / 3600.0 AS hours_since_last_click
    FROM stg_events
    WHERE conversion_id IS NOT NULL
      AND time_since_last_click IS NOT NULL
      AND time_since_last_click > 0
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
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY (conversion_ts - ts)) / 3600.0, 2) AS p25_hours,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY (conversion_ts - ts)) / 3600.0, 2) AS p50_hours,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY (conversion_ts - ts)) / 3600.0, 2) AS p75_hours,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY (conversion_ts - ts)) / 3600.0, 2) AS p90_hours,
    COUNT(DISTINCT conversion_id) AS total_conversions
FROM stg_events
WHERE conversion_id IS NOT NULL
  AND conversion_ts IS NOT NULL
  AND (conversion_ts - ts) >= 0;
