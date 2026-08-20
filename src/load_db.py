"""
Load the deliveries and matches tables into SQLite and run the analysis
queries.

Writes data/ipl.db and reports/sql_results.md.
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "ipl.db"
SQL_PATH = ROOT / "sql" / "analysis.sql"
OUT_PATH = ROOT / "reports" / "sql_results.md"

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_del_batter ON deliveries(batter);
CREATE INDEX IF NOT EXISTS idx_del_bowler ON deliveries(bowler);
CREATE INDEX IF NOT EXISTS idx_del_phase  ON deliveries(phase);
CREATE INDEX IF NOT EXISTS idx_del_season ON deliveries(season_year);
CREATE INDEX IF NOT EXISTS idx_del_match  ON deliveries(match_id);
CREATE INDEX IF NOT EXISTS idx_mat_season ON matches(season_year);
"""


def split_queries(text: str) -> list[tuple[str, str]]:
    """Split the SQL file into (title, statement) pairs on '-- Qn.' markers."""
    queries = []
    for block in re.split(r"\n(?=-- Q\d+\.)", text):
        if not block.strip().startswith("-- Q"):
            continue
        lines = block.strip().splitlines()
        title = lines[0].lstrip("- ").strip()
        sql = "\n".join(l for l in lines if not l.strip().startswith("--"))
        if sql.strip():
            queries.append((title, sql.strip()))
    return queries


def main() -> None:
    deliveries = pd.read_csv(PROCESSED_DIR / "deliveries.csv", dtype={"season": str})
    matches = pd.read_csv(PROCESSED_DIR / "matches.csv", dtype={"season": str})

    with sqlite3.connect(DB_PATH) as conn:
        deliveries.to_sql("deliveries", conn, if_exists="replace", index=False)
        matches.to_sql("matches", conn, if_exists="replace", index=False)
        conn.executescript(INDEXES)

        n_del = conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
        n_mat = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        print(f"Loaded {n_del:,} deliveries and {n_mat:,} matches "
              f"into {DB_PATH.name}\n")

        out = [
            "# SQL Analysis Results",
            "",
            f"Source: `sql/analysis.sql` against `{DB_PATH.name}`",
            "",
        ]
        for title, sql in split_queries(SQL_PATH.read_text(encoding="utf-8")):
            frame = pd.read_sql_query(sql, conn)
            print(f"{title}  ->  {len(frame)} rows")

            # Some queries return long tables; show a sample rather than
            # hundreds of rows of markdown.
            shown = frame.head(20) if len(frame) > 40 else frame
            note = (
                f"\n_Showing first 20 of {len(frame)} rows._\n"
                if len(frame) > 40 else ""
            )
            out += [f"## {title}", "", shown.to_markdown(index=False), note, ""]

    OUT_PATH.write_text("\n".join(out), encoding="utf-8")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
