"""Debug script to isolate the CREATE VIEW issue."""
import duckdb

con = duckdb.connect("criteo.duckdb")

# Test 1: Can we query raw_sample?
print("Test 1 - raw_sample row count:")
r = con.execute("SELECT COUNT(*) FROM raw_sample")
print(r.fetchdf())

# Test 2: Simple CREATE VIEW
print("\nTest 2 - simple CREATE OR REPLACE VIEW:")
con.execute("CREATE OR REPLACE VIEW test_v AS SELECT 1 AS x")
print("  OK")

# Test 3: CREATE VIEW with quoted timestamp column
print("\nTest 3 - CREATE VIEW with 'timestamp' column:")
stmt = """CREATE OR REPLACE VIEW stg_events AS
SELECT
    "timestamp"                          AS ts,
    "timestamp" // 86400                 AS day_idx,
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
FROM raw_sample"""
try:
    con.execute(stmt)
    print("  OK")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 4: same but with executescript / sql()
print("\nTest 4 - using duckdb.sql() style:")
try:
    con.sql(stmt)
    print("  OK")
except Exception as e:
    print(f"  ERROR: {e}")

con.close()
