-- Block 1: Load the Criteo dataset.
-- The default run uses all users. `python run_all.py --sample-users` enables
-- the optional deterministic 5% user sample without breaking user journeys.

CREATE OR REPLACE TABLE raw_sample AS
SELECT *
FROM read_csv('data/criteo_attribution_dataset.tsv.gz',
              delim = E'\t', header = true)
WHERE 1 = 1
/* SAMPLE_USERS_FILTER */;
-- Inspect schema and data types
DESCRIBE raw_sample;

-- Check size
SELECT
    COUNT(*)              AS n_rows,
    COUNT(DISTINCT uid)   AS n_users,
    COUNT(DISTINCT campaign) AS n_campaigns
FROM raw_sample;
