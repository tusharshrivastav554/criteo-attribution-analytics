-- ============================================================
-- Future Plan Item 1: Attribution Model Comparison
-- ============================================================
-- Assign fractional credit for each conversion under four rules:
--   last-touch  : 100% to the most recent impression before conversion
--   first-touch : 100% to the earliest impression in the path
--   linear      : equal share across every touchpoint
--   time-decay  : exponential weight, half-life = 7 days (604800 s)
--
-- Input : stg_events view (created in 02_staging.sql)
-- Output: results/attribution_model_comparison.csv
--         results/attribution_rank_shifts.csv
-- ============================================================

-- Step 1: Collect all touchpoints per conversion path.
CREATE OR REPLACE TABLE attr_paths AS
SELECT
    conversion_id,
    uid,
    campaign,
    ts,
    click,
    conversion_ts,
    ROW_NUMBER() OVER (PARTITION BY conversion_id ORDER BY ts ASC)  AS touch_seq,
    COUNT(*)      OVER (PARTITION BY conversion_id)                  AS path_length,
    MAX(ts)       OVER (PARTITION BY conversion_id)                  AS last_touch_ts,
    MIN(ts)       OVER (PARTITION BY conversion_id)                  AS first_touch_ts
FROM stg_events
WHERE conversion_id IS NOT NULL
  AND conversion_id > 0
  AND conversion_ts IS NOT NULL;

SELECT COUNT(*) AS touchpoints_in_paths,
       COUNT(DISTINCT conversion_id) AS conversions_in_paths,
       ROUND(AVG(path_length), 2) AS avg_path_length
FROM attr_paths;

-- Step 2: Per-touchpoint credit weight under each model.
CREATE OR REPLACE TABLE attr_weights AS
SELECT
    conversion_id,
    campaign,
    ts,
    touch_seq,
    path_length,
    last_touch_ts,
    -- Last-touch: full credit to the final touchpoint
    CASE WHEN touch_seq = path_length THEN 1.0 ELSE 0.0 END  AS w_last,
    -- First-touch: full credit to the first touchpoint
    CASE WHEN touch_seq = 1           THEN 1.0 ELSE 0.0 END  AS w_first,
    -- Linear: equal split
    1.0 / path_length                                          AS w_linear,
    -- Time-decay: true seven-day half-life; normalised within each conversion
    EXP(-LN(2) * (last_touch_ts - ts) / 604800.0) /
        SUM(EXP(-LN(2) * (last_touch_ts - ts) / 604800.0))
            OVER (PARTITION BY conversion_id)                  AS w_timedecay
FROM attr_paths;

-- Step 3: Roll up to campaign level.
CREATE OR REPLACE TABLE res_attribution_models AS
SELECT
    campaign,
    ROUND(SUM(w_last),      4) AS credit_last_touch,
    ROUND(SUM(w_first),     4) AS credit_first_touch,
    ROUND(SUM(w_linear),    4) AS credit_linear,
    ROUND(SUM(w_timedecay), 4) AS credit_time_decay,
    RANK() OVER (ORDER BY SUM(w_last)      DESC) AS rank_last,
    RANK() OVER (ORDER BY SUM(w_first)     DESC) AS rank_first,
    RANK() OVER (ORDER BY SUM(w_linear)    DESC) AS rank_linear,
    RANK() OVER (ORDER BY SUM(w_timedecay) DESC) AS rank_timedecay
FROM attr_weights
GROUP BY campaign
ORDER BY credit_last_touch DESC;

COPY res_attribution_models TO 'results/attribution_model_comparison.csv' (HEADER, DELIMITER ',');

-- Step 4: Rank-shift table — campaigns most sensitive to measurement rule.
CREATE OR REPLACE TABLE res_attribution_rank_shifts AS
SELECT
    campaign,
    rank_last,
    rank_first,
    rank_linear,
    rank_timedecay,
    ABS(rank_last - rank_first)      AS shift_last_vs_first,
    ABS(rank_last - rank_timedecay)  AS shift_last_vs_timedecay,
    GREATEST(
        ABS(rank_last - rank_first),
        ABS(rank_last - rank_linear),
        ABS(rank_last - rank_timedecay)
    )                                AS max_rank_shift
FROM res_attribution_models
ORDER BY max_rank_shift DESC;

COPY res_attribution_rank_shifts TO 'results/attribution_rank_shifts.csv' (HEADER, DELIMITER ',');

SELECT campaign, credit_last_touch, credit_first_touch, credit_linear, credit_time_decay,
       rank_last, rank_first, rank_linear, rank_timedecay
FROM res_attribution_models LIMIT 10;
