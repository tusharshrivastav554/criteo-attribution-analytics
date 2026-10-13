-- Block 1: Load a 5% sample of USERS from the Criteo dataset.
-- We sample by user (uid), not by row, so each user's full journey remains intact.
-- Hashing uid and taking rows where hash % 20 = 0 gives ~5% of users deterministically.

CREATE OR REPLACE TABLE raw_sample AS
SELECT *
FROM read_csv('data/criteo_attribution_dataset.tsv.gz',
              delim = E'\t', header = true)
-- WHERE hash(uid) % 20 = 0;
-- LIMIT 1000;
;
-- Inspect schema and data types
DESCRIBE raw_sample;

-- Check size
SELECT
    COUNT(*)              AS n_rows,
    COUNT(DISTINCT uid)   AS n_users,
    COUNT(DISTINCT campaign) AS n_campaigns
FROM raw_sample;
