-- Block 3a: Spend efficiency by campaign.
-- Question: Which campaigns are most/least efficient, and where is spend going?
--
-- Key design choices:
--   - Only include campaigns with >= 1000 impressions (enough volume to be meaningful).
--   - Campaign conversion metrics are one row per (campaign, conversion_id).
--     Campaign credit is retained, while global denominators use distinct IDs.
--   - cost and cpo are transformed; use for relative comparison only.

CREATE OR REPLACE TABLE res_campaign AS
WITH base AS (
    SELECT
        campaign,
        COUNT(*)                                                           AS impressions,
        SUM(click)                                                         AS clicks,
        SUM(cost)                                                          AS total_cost,
        COUNT(DISTINCT CASE WHEN attribution = 1 AND conversion_id IS NOT NULL
                            THEN conversion_id END)                          AS attributed_conversions
    FROM stg_events
    GROUP BY campaign
    HAVING COUNT(*) >= 1000     -- minimum volume threshold; stated in memo
), campaign_totals AS (
    SELECT SUM(attributed_conversions) AS portfolio_attributed_conversions
    FROM base
)
SELECT
    b.*,
    b.clicks * 1.0 / b.impressions                                             AS ctr,
    b.total_cost / NULLIF(b.attributed_conversions, 0)                         AS cost_per_attr_conv,
    b.total_cost / SUM(b.total_cost) OVER ()                                   AS spend_share,
    b.attributed_conversions * 1.0 / NULLIF(t.portfolio_attributed_conversions, 0) AS conv_share,
    RANK() OVER (ORDER BY b.total_cost / NULLIF(b.attributed_conversions, 0))  AS efficiency_rank
FROM base b
CROSS JOIN campaign_totals t
ORDER BY efficiency_rank;

-- Save to CSV
COPY res_campaign TO 'results/campaign_performance.csv' (HEADER, DELIMITER ',');

-- Quick sanity: row count
SELECT COUNT(*) AS n_campaigns_in_result FROM res_campaign;
