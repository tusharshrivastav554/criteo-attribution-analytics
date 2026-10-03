-- Block 3a: Spend efficiency by campaign.
-- Question: Which campaigns are most/least efficient, and where is spend going?
--
-- Key design choices:
--   - Only include campaigns with >= 1000 impressions (enough volume to be meaningful).
--   - Conversions = COUNT(DISTINCT conversion_id) where attribution=1, not SUM(conversion flag).
--   - cost and cpo are transformed; use for relative comparison only.

CREATE OR REPLACE TABLE res_campaign AS
WITH base AS (
    SELECT
        campaign,
        COUNT(*)                                                           AS impressions,
        SUM(click)                                                         AS clicks,
        SUM(cost)                                                          AS total_cost,
        COUNT(DISTINCT CASE WHEN attribution = 1 THEN conversion_id END)   AS attributed_conversions
    FROM stg_events
    GROUP BY campaign
    HAVING COUNT(*) >= 1000     -- minimum volume threshold; stated in memo
)
SELECT
    *,
    clicks * 1.0 / impressions                                             AS ctr,
    total_cost / NULLIF(attributed_conversions, 0)                         AS cost_per_attr_conv,
    total_cost / SUM(total_cost) OVER ()                                   AS spend_share,
    attributed_conversions * 1.0 / NULLIF(SUM(attributed_conversions) OVER (), 0) AS conv_share,
    RANK() OVER (ORDER BY total_cost / NULLIF(attributed_conversions, 0))  AS efficiency_rank
FROM base
ORDER BY efficiency_rank;

-- Save to CSV
COPY res_campaign TO 'results/campaign_performance.csv' (HEADER, DELIMITER ',');

-- Quick sanity: row count
SELECT COUNT(*) AS n_campaigns_in_result FROM res_campaign;
