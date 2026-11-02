"""Generate a synthetic e-commerce orders dataset (CSV) for the warehouse project.

Usage: python generate_data.py --rows 50000 --out data/orders.csv
"""
import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

REGIONS = {
    "South": ["Chennai", "Bengaluru", "Hyderabad", "Kochi"],
    "North": ["Delhi", "Jaipur", "Lucknow", "Chandigarh"],
    "West": ["Mumbai", "Pune", "Ahmedabad", "Surat"],
    "East": ["Kolkata", "Bhubaneswar", "Patna", "Guwahati"],
}
CATALOG = {
    "Electronics": [("Wireless Earbuds", 2499), ("Smart Watch", 4999), ("Power Bank", 1299), ("Bluetooth Speaker", 1999)],
    "Fashion": [("Running Shoes", 2999), ("Denim Jacket", 2199), ("Backpack", 1499), ("Sunglasses", 999)],
    "Home": [("Mixer Grinder", 3499), ("Air Fryer", 5499), ("Bedsheet Set", 1199), ("LED Lamp", 699)],
    "Books": [("Python Handbook", 599), ("SQL Essentials", 499), ("Data Engineering Guide", 899)],
}
SEGMENTS = ["Consumer", "Corporate", "Home Office"]
CHANNELS = ["Web", "Mobile App", "Marketplace"]

HEADER = [
    "order_id", "order_date", "customer_id", "customer_name", "segment",
    "region", "city", "product_id", "product_name", "category",
    "unit_price", "quantity", "discount_pct", "channel",
]


def build(rows: int, seed: int = 42):
    rnd = random.Random(seed)
    products = []
    pid = 1
    for cat, items in CATALOG.items():
        for name, price in items:
            products.append((f"P{pid:03d}", name, cat, price))
            pid += 1
    n_customers = max(200, rows // 20)
    customers = []
    for i in range(1, n_customers + 1):
        region = rnd.choice(list(REGIONS))
        customers.append((f"C{i:05d}", f"Customer {i}", rnd.choice(SEGMENTS), region, rnd.choice(REGIONS[region])))
    start = date(2024, 1, 1)
    span = 730
    for n in range(1, rows + 1):
        cust = rnd.choice(customers)
        prod = rnd.choice(products)
        d = start + timedelta(days=rnd.randint(0, span - 1))
        yield [
            f"O{n:07d}", d.isoformat(), cust[0], cust[1], cust[2], cust[3], cust[4],
            prod[0], prod[1], prod[2], prod[3], rnd.randint(1, 5),
            rnd.choice([0, 0, 0, 5, 10, 15]), rnd.choice(CHANNELS),
        ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=50000)
    ap.add_argument("--out", default="data/orders.csv")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(build(args.rows, args.seed))
    print(f"Wrote {args.rows} rows to {out}")


if __name__ == "__main__":
    main()
