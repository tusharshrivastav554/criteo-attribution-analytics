-- Block 3d: Reconciliation checks — verify our result tables match staging.
-- Do NOT skip. Every number in the memo must be validated here.

-- ─── Check 1: Campaign table impressions vs staging impressions ──────────────
-- These should match for campaigns that passed the >=1000 threshold.
SELECT
    (SELECT SUM(impressions) FROM res_campaign)                        AS campaign_table_impr,
    (SELECT COUNT(*)
     FROM stg_events
     WHERE campaign IN (SELECT campaign FROM res_campaign))            AS staging_impr_same_campaigns;

-- ─── Check 2: No duplicate campaigns in funnel table ────────────────────────
-- Expect zero rows returned.
SELECT campaign, COUNT(*) AS cnt
FROM res_funnel
GROUP BY campaign
HAVING COUNT(*) > 1;

-- ─── Check 3: Manual spot-check for one high-volume campaign ────────────────
-- We pick the top campaign by impressions to verify cost and attributed conversions.
WITH top1 AS (
    SELECT campaign FROM res_campaign ORDER BY impressions DESC LIMIT 1
)
SELECT
    s.campaign,
    SUM(s.cost)                                                         AS staging_total_cost,
    r.total_cost                                                        AS table_total_cost,
    COUNT(DISTINCT CASE WHEN s.attribution = 1 AND s.conversion_id IS NOT NULL
                        THEN s.conversion_id END)                        AS staging_attr_conv,
    r.attributed_conversions                                            AS table_attr_conv
FROM stg_events s
JOIN res_campaign r USING (campaign)
WHERE s.campaign IN (SELECT campaign FROM top1)
GROUP BY s.campaign, r.total_cost, r.attributed_conversions;

-- ─── Check 4: Funnel and campaign tables agree on attributed conversions ─────
-- For campaigns present in both tables, attributed conversion counts should match.
SELECT
    f.campaign,
    f.attributed_conversions    AS funnel_attr_conv,
    c.attributed_conversions    AS campaign_attr_conv,
    f.attributed_conversions - c.attributed_conversions AS diff
FROM res_funnel f
JOIN res_campaign c USING (campaign)
WHERE f.attributed_conversions <> c.attributed_conversions
ORDER BY ABS(diff) DESC
LIMIT 10;

-- ─── Check 5: Campaign credit vs global conversion count ─────────────────────
-- A conversion may be credited to multiple campaigns.  Keep the two measures
-- explicit so campaign credit is not mistaken for a global conversion total.
SELECT
    COUNT(DISTINCT CASE WHEN s.attribution = 1 AND s.conversion_id IS NOT NULL
                        THEN s.conversion_id END) AS global_attr_conversions,
    (SELECT SUM(attributed_conversions) FROM res_campaign) AS campaign_attr_credit
FROM stg_events s
;

-- ─── Check 6: Frequency table pair counts sum to total user-campaign pairs ───
SELECT
    (SELECT SUM(user_campaign_pairs) FROM res_frequency)          AS freq_table_pairs,
    (SELECT COUNT(DISTINCT uid || '-' || CAST(campaign AS VARCHAR))
     FROM stg_events)                                             AS staging_uc_pairs;
