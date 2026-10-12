-- Block 2: Build a clean staging view from raw_sample.
-- Converts -1 placeholders to NULL so they don't corrupt averages or comparisons.
-- Adds day_idx (assuming timestamp unit is seconds over ~30 days).

CREATE OR REPLACE VIEW stg_events AS
SELECT
    "timestamp"                          AS ts,
    "timestamp" // 86400                 AS day_idx,          -- day number (confirm unit is seconds)
    uid,
    campaign,
    conversion,
    NULLIF(conversion_timestamp, -1)     AS conversion_ts,
    NULLIF(conversion_id, -1)            AS conversion_id,
    attribution,
    click,
    NULLIF(click_pos, -1)                AS click_pos,
    NULLIF(click_nb, -1)                 AS click_nb,
    cost,
    cpo,
    NULLIF(time_since_last_click, -1)    AS time_since_last_click
FROM raw_sample;

-- ─── Sanity check 1: Overall shape ──────────────────────────────────────────
SELECT  
    COUNT(*)                              AS impressions,
    COUNT(DISTINCT uid)                   AS users,
    COUNT(DISTINCT campaign)              AS campaigns,
    SUM(click)                            AS clicks,
    SUM(conversion)                       AS conversion_flag_rows,
    COUNT(DISTINCT conversion_id)         AS distinct_conversions,
    SUM(attribution)                      AS attribution_flag_rows
FROM stg_events;

-- ─── Sanity check 2: Does one conversion_id appear on many impression rows? ─
-- If rows_per_conversion > 1 commonly, we must use COUNT(DISTINCT conversion_id).
SELECT conversion_id, COUNT(*) AS rows_per_conversion
FROM stg_events
WHERE conversion_id IS NOT NULL
GROUP BY conversion_id
ORDER BY rows_per_conversion DESC
LIMIT 10;

-- ─── Sanity check 3: Timestamp range ────────────────────────────────────────
-- Expect ~30 days if unit is seconds (2_592_000 seconds ≈ 30 days).
SELECT
    MIN(ts)      AS ts_min,
    MAX(ts)      AS ts_max,
    MAX(day_idx) AS max_day
FROM stg_events;
