"""
Cryptocurrency Price Tracker — analyze.py
==========================================
Reads crypto_prices.csv and prints:
  • Latest snapshot summary
  • Best / worst 24-h performers
  • Per-coin price history (min / max / avg)

Run:
    python analyze.py
    python analyze.py --file my_data.csv
"""

import argparse
import csv
import os
from collections import defaultdict


def load_csv(filepath):
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"CSV not found: {filepath}")
    with open(filepath, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_float(text):
    """Strip $, %, +, commas, T/B/M suffixes and return a float or None."""
    if not text or text.strip() in ("N/A", ""):
        return None
    t = text.strip().lstrip("$+").replace(",", "")
    multiplier = 1
    if t.endswith("T"):
        multiplier, t = 1e12, t[:-1]
    elif t.endswith("B"):
        multiplier, t = 1e9,  t[:-1]
    elif t.endswith("M"):
        multiplier, t = 1e6,  t[:-1]
    t = t.rstrip("%")
    try:
        return float(t) * multiplier
    except ValueError:
        return None


def analyze(rows):
    if not rows:
        print("No data found in CSV.")
        return

    # Group by timestamp, then by coin name
    by_ts   = defaultdict(list)
    by_name = defaultdict(list)
    for r in rows:
        by_ts[r["Timestamp"]].append(r)
        by_name[r["Name"]].append(r)

    timestamps = sorted(by_ts.keys())
    latest_ts  = timestamps[-1]
    latest     = by_ts[latest_ts]

    # ── Latest snapshot ─────────────────────────────────────────
    print("=" * 60)
    print(f"  LATEST SNAPSHOT  —  {latest_ts}")
    print("=" * 60)
    print(f"{'Coin':<14}{'Symbol':<8}{'Price':>14}{'24h Δ':>10}{'Market Cap':>16}")
    print("-" * 60)
    for r in sorted(latest, key=lambda x: parse_float(x.get("Market Cap")) or 0, reverse=True):
        chg = parse_float(r.get("24h Change (%)"))
        arrow = "▲" if chg and chg > 0 else ("▼" if chg and chg < 0 else " ")
        print(f"{r['Name']:<14}{r['Symbol']:<8}{r['Price (USD)']:>14}"
              f"{arrow + r.get('24h Change (%)', 'N/A'):>10}{r.get('Market Cap','N/A'):>16}")

    # ── Best / worst performers ──────────────────────────────────
    ranked = [(r["Name"], parse_float(r.get("24h Change (%)")))
              for r in latest if parse_float(r.get("24h Change (%)")) is not None]
    ranked.sort(key=lambda x: x[1], reverse=True)

    print("\n  📈  TOP GAINER   :", ranked[0][0] if ranked else "—",
          f"  {ranked[0][1]:+.2f}%" if ranked else "")
    print("  📉  TOP LOSER    :", ranked[-1][0] if ranked else "—",
          f"  {ranked[-1][1]:+.2f}%" if ranked else "")

    # ── Per-coin price history ───────────────────────────────────
    print(f"\n{'='*60}")
    print("  PRICE HISTORY SUMMARY  (all recorded snapshots)")
    print("=" * 60)
    print(f"{'Coin':<14}{'Entries':>8}{'Min Price':>14}{'Max Price':>14}{'Avg Price':>14}")
    print("-" * 60)
    for name, coin_rows in sorted(by_name.items()):
        prices = [parse_float(r["Price (USD)"]) for r in coin_rows
                  if parse_float(r["Price (USD)"]) is not None]
        if not prices:
            continue
        print(f"{name:<14}{len(prices):>8}"
              f"{min(prices):>14,.4g}"
              f"{max(prices):>14,.4g}"
              f"{sum(prices)/len(prices):>14,.4g}")

    print(f"\n  Total snapshots : {len(timestamps)}")
    print(f"  First recorded  : {timestamps[0]}")
    print(f"  Last recorded   : {timestamps[-1]}")
    print(f"  Total rows      : {len(rows)}\n")


def main():
    parser = argparse.ArgumentParser(description="Analyze crypto_prices.csv")
    parser.add_argument("--file", default="crypto_prices.csv",
                        help="Path to CSV file (default: crypto_prices.csv)")
    args = parser.parse_args()

    print(f"\nLoading: {args.file}")
    rows = load_csv(args.file)
    analyze(rows)


if __name__ == "__main__":
    main()
