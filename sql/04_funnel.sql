-- Block 3b: Funnel analysis by campaign.
-- Question: Where does the funnel leak, and how many conversions happen without a click?
--
-- Note: Funnel stages are not strictly nested.
--   - A conversion can happen after a view with no click (post-view conversion).
--   - share_conversions_with_click shows the click-driven vs view-driven split.

CREATE OR REPLACE TABLE res_funnel AS
WITH imp AS (
    -- Impressions and clicks per campaign
    SELECT
        campaign,
        COUNT(*)  AS impressions,
        SUM(click) AS clicks
    FROM stg_events
    GROUP BY campaign
),
conv AS (
    -- One row per (campaign, conversion_id): did it have attribution? a click?
    SELECT
        campaign,
        conversion_id,
        MAX(attribution) AS attributed,
        MAX(click)       AS had_click   -- 1 if any impression in this path was clicked
    FROM stg_events
    WHERE conversion_id IS NOT NULL
      AND conversion_id > 0
    GROUP BY campaign, conversion_id
),
conv_agg AS (
    SELECT
        campaign,
        COUNT(*)        AS conversions,
        SUM(attributed) AS attributed_conversions,
        SUM(had_click)  AS conversions_with_click
    FROM conv
    GROUP BY campaign
)
SELECT
    i.campaign,
    i.impressions,
    i.clicks,
    COALESCE(c.conversions, 0)                          AS conversions,
    COALESCE(c.attributed_conversions, 0)               AS attributed_conversions,
    COALESCE(c.conversions_with_click, 0) * 1.0
        / NULLIF(c.conversions, 0)                      AS share_conversions_with_click
FROM imp i
LEFT JOIN conv_agg c USING (campaign)
WHERE i.impressions >= 1000
ORDER BY i.impressions DESC;

-- Save to CSV
COPY res_funnel TO 'results/funnel_by_campaign.csv' (HEADER, DELIMITER ',');

-- Sanity: row count
SELECT COUNT(*) AS n_campaigns_in_funnel FROM res_funnel;
