"""Validate the data and the analytical SQL locally with SQLite (standard library, no installs).

This checks data integrity and that the logic of sql/03_analytics.sql is valid. It swaps
BigQuery's DATE_TRUNC(order_date, MONTH) for the SQLite equivalent. It does NOT test
BigQuery-specific DDL (partitioning/clustering) - that only runs in BigQuery.

Usage: python local_validate.py --csv data/orders.csv
"""
import argparse
import csv
import re
import sqlite3
from pathlib import Path


def load(con: sqlite3.Connection, csv_path: str) -> None:
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        con.execute(f"CREATE TABLE stg_orders ({', '.join(cols)})")
        placeholders = ",".join("?" for _ in cols)
        con.executemany(
            f"INSERT INTO stg_orders VALUES ({placeholders})",
            ([row[c] for c in cols] for row in reader),
        )
    # Same fact-table logic as sql/02_star_schema.sql
    con.execute(
        """
        CREATE TABLE fact_sales AS
        SELECT order_id, order_date, customer_id, product_id, region, city, category, channel,
               CAST(quantity AS INTEGER) AS quantity,
               CAST(unit_price AS REAL) AS unit_price,
               CAST(discount_pct AS INTEGER) AS discount_pct,
               ROUND(CAST(quantity AS INTEGER) * CAST(unit_price AS REAL)
                     * (1 - CAST(discount_pct AS REAL) / 100.0), 2) AS net_revenue
        FROM stg_orders
        """
    )


def to_sqlite(q: str) -> str:
    q = "\n".join(line for line in q.splitlines() if not line.strip().startswith("--"))
    return q.replace("DATE_TRUNC(order_date, MONTH)", "strftime('%Y-%m-01', order_date)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/orders.csv")
    args = ap.parse_args()

    con = sqlite3.connect(":memory:")
    load(con, args.csv)

    n = con.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    dup = con.execute("SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM fact_sales").fetchone()[0]
    nulls = con.execute(
        "SELECT COUNT(*) FROM fact_sales WHERE customer_id IS NULL OR product_id IS NULL OR order_date IS NULL"
    ).fetchone()[0]
    neg = con.execute("SELECT COUNT(*) FROM fact_sales WHERE net_revenue <= 0").fetchone()[0]
    print(f"rows={n} duplicate_order_ids={dup} null_keys={nulls} non_positive_revenue={neg}")
    assert n > 0 and dup == 0 and nulls == 0 and neg == 0, "data checks failed"

    sql_text = Path("sql/03_analytics.sql").read_text()
    queries = [q.strip() for q in re.split(r";\s*\n", sql_text) if "SELECT" in q]
    assert len(queries) == 4, f"expected 4 queries, found {len(queries)}"
    for i, q in enumerate(queries, 1):
        cur = con.execute(to_sqlite(q))
        rows = cur.fetchall()
        header = [d[0] for d in cur.description]
        print(f"\n--- Query {i}: {len(rows)} rows ---")
        print(" | ".join(header))
        for r in rows[:5]:
            print(" | ".join(str(x) for x in r))
        assert rows, f"query {i} returned no rows"
    print("\nAll local checks passed.")


if __name__ == "__main__":
    main()
