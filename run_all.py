"""
run_all.py — Execute all SQL analysis scripts in order using DuckDB.

Usage:
    python run_all.py

The script connects to (or creates) criteo.duckdb, then runs every
sql/0*.sql file alphabetically. Each statement's output is printed
so you can verify row counts and sanity checks inline.

If a multi-statement file errors in Python, run it directly:
    duckdb criteo.duckdb < sql/02_staging.sql
"""

import io
import argparse
import pathlib
import sys

import duckdb

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DB_PATH = "criteo.duckdb"
SQL_DIR = pathlib.Path("sql")
SAMPLE_MARKER = "/* SAMPLE_USERS_FILTER */"


def run_file(
    con: duckdb.DuckDBPyConnection,
    path: pathlib.Path,
    sql_override: str | None = None,
) -> None:
    """Execute all statements in a SQL file and print results."""
    print(f"\n{'='*60}")
    print(f"Running {path.name}")
    print("=" * 60)
    sql = sql_override if sql_override is not None else path.read_text(encoding="utf-8")

    # Robust split: strip the "-- comment" tail of each line before splitting on ';'
    # This prevents semicolons inside inline comments from breaking statements.
    def split_statements(sql_text: str) -> list[str]:
        stmts, current = [], []
        for line in sql_text.splitlines():
            # Find '--' comment start (outside of any string literal for our purposes)
            idx = line.find("--")
            code_part = line[:idx] if idx != -1 else line
            current.append(line)
            if ";" in code_part:
                stmts.append("\n".join(current))
                current = []
        if current:
            leftover = "\n".join(current).strip()
            if leftover:
                stmts.append(leftover)
        return [s.strip() for s in stmts if s.strip()]

    statements = split_statements(sql)
    for stmt in statements:
        # Skip pure comment blocks
        clean = "\n".join(
            line for line in stmt.splitlines() if not line.strip().startswith("--")
        ).strip()
        if not clean:
            continue
        try:
            result = con.execute(clean)   # use comment-stripped version
            if result is not None:
                df = result.fetchdf()
                if not df.empty:
                    print(df.to_string(index=False))
                    print(f"  -> {len(df)} row(s)")
        except Exception as exc:
            print(f"  ERROR in statement:\n  {clean[:300]}\n  {exc}", file=sys.stderr)
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the DuckDB attribution pipeline.")
    parser.add_argument(
        "--sample-users",
        action="store_true",
        help="Restrict the load step to a deterministic 5%% user sample.",
    )
    args = parser.parse_args()
    con = duckdb.connect(DB_PATH)
    sql_files = sorted(SQL_DIR.glob("0*.sql"))
    if not sql_files:
        print("No SQL files found in sql/. Check the directory.", file=sys.stderr)
        sys.exit(1)

    for f in sql_files:
        sql_override = None
        if f.name == "01_load_sample.sql":
            sql_override = f.read_text(encoding="utf-8").replace(
                SAMPLE_MARKER,
                "AND hash(uid) % 20 = 0" if args.sample_users else "",
            )
        run_file(con, f, sql_override=sql_override)

    print("\n✓ All SQL scripts completed successfully.")
    con.close()


if __name__ == "__main__":
    main()
