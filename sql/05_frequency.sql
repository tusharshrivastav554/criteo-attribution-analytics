-- Block 3c: Frequency analysis — does conversion rate change with ad frequency?
-- Question: Is there a frequency sweet spot, or a point of diminishing returns?
--
-- Work at the USER-CAMPAIGN level (not impression-by-impression).
-- "converted" = 1 if the user had any conversion (via any impression) in this campaign.
--
-- Caveats (must state in memo):
--   1. Correlation only: high-frequency users may have higher intent, not more ad exposure effect.
--   2. Small buckets = noisy rates; report pair counts alongside rates.

CREATE OR REPLACE TABLE res_frequency AS
WITH uc AS (
    -- One row per (user, campaign): their impression count and whether they converted
    SELECT
        uid,
        campaign,
        COUNT(*)  AS impressions,
        MAX(CASE WHEN conversion_id IS NOT NULL THEN 1 ELSE 0 END) AS converted
    FROM stg_events
    GROUP BY uid, campaign
)
SELECT
    CASE
        WHEN impressions = 1   THEN '1'
        WHEN impressions = 2   THEN '2'
        WHEN impressions <= 4  THEN '3-4'
        WHEN impressions <= 9  THEN '5-9'
        ELSE '10+'
    END                  AS freq_bucket,
    MIN(impressions)     AS bucket_order,   -- for deterministic sort
    COUNT(*)             AS user_campaign_pairs,
    AVG(converted)       AS conv_rate
FROM uc
GROUP BY 1
ORDER BY bucket_order;

-- Save to CSV
COPY res_frequency TO 'results/frequency_buckets.csv' (HEADER, DELIMITER ',');

-- Optional: same breakdown for top 5 campaigns by volume
CREATE OR REPLACE TABLE res_frequency_top5 AS
WITH top5 AS (
    SELECT campaign
    FROM stg_events
    GROUP BY campaign
    ORDER BY COUNT(*) DESC
    LIMIT 5
),
uc AS (
    SELECT
        uid,
        campaign,
        COUNT(*)  AS impressions,
        MAX(CASE WHEN conversion_id IS NOT NULL THEN 1 ELSE 0 END) AS converted
    FROM stg_events
    WHERE campaign IN (SELECT campaign FROM top5)
    GROUP BY uid, campaign
)
SELECT
    campaign,
    CASE
        WHEN impressions = 1   THEN '1'
        WHEN impressions = 2   THEN '2'
        WHEN impressions <= 4  THEN '3-4'
        WHEN impressions <= 9  THEN '5-9'
        ELSE '10+'
    END                  AS freq_bucket,
    MIN(impressions)     AS bucket_order,
    COUNT(*)             AS user_campaign_pairs,
    AVG(converted)       AS conv_rate
FROM uc
GROUP BY campaign, 2
ORDER BY campaign, bucket_order;

COPY res_frequency_top5 TO 'results/frequency_top5_campaigns.csv' (HEADER, DELIMITER ',');

SELECT * FROM res_frequency;
