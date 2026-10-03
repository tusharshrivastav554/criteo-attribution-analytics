"""Inspect exactly what statements run_all.py produces from 02_staging.sql."""
import pathlib

sql = pathlib.Path("sql/02_staging.sql").read_text(encoding="utf-8")
statements = [s.strip() for s in sql.split(";") if s.strip()]

print(f"Total statements after split: {len(statements)}\n")
for i, stmt in enumerate(statements):
    clean = "\n".join(
        line for line in stmt.splitlines() if not line.strip().startswith("--")
    ).strip()
    print(f"--- Statement {i+1} (first 300 chars of clean) ---")
    print(repr(clean[:300]))
    print()
