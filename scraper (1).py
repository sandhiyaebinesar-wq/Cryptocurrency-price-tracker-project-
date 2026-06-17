"""
Cryptocurrency Price Tracker — scraper.py
==========================================
Fetches real-time data from CoinGecko (free API, no key needed).
Falls back to Selenium / CoinMarketCap if you set USE_SELENIUM = True.

Run:
    python scraper.py               # fetch once
    python scraper.py --loop 60     # fetch every 60 seconds
"""

import argparse
import csv
import os
import time
from datetime import datetime

import requests

# ── Config ─────────────────────────────────────────────────────────────────
CSV_FILE    = "crypto_prices.csv"
TOP_N       = 10
CURRENCY    = "usd"
USE_SELENIUM = False   # flip to True to use Selenium instead of API

# Optional filters (set to None to disable)
PRICE_FILTER = None   # e.g. 1.0 → only coins priced above $1
MIN_CHANGE   = None   # e.g. 2.0 → only coins with 24h change > +2 %

API_URL = "https://api.coingecko.com/api/v3/coins/markets"

CSV_HEADER = [
    "Timestamp", "Name", "Symbol",
    "Price (USD)", "1h Change (%)", "24h Change (%)", "7d Change (%)",
    "Market Cap", "Volume (24h)",
]

# ── Helpers ─────────────────────────────────────────────────────────────────

def fmt_price(val):
    if val is None:
        return "N/A"
    if val >= 1:
        return f"${val:,.2f}"
    return f"${val:.6f}"


def fmt_pct(val):
    if val is None:
        return "N/A"
    return f"{val:+.2f}%"


def fmt_large(val):
    if val is None:
        return "N/A"
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    if val >= 1e9:
        return f"${val/1e9:.2f}B"
    if val >= 1e6:
        return f"${val/1e6:.2f}M"
    return f"${val:,.0f}"


# ── Fetch via CoinGecko REST API ─────────────────────────────────────────────

def fetch_via_api(top_n=TOP_N):
    """Return list of coin dicts from CoinGecko public API."""
    params = {
        "vs_currency":            CURRENCY,
        "order":                  "market_cap_desc",
        "per_page":               top_n,
        "page":                   1,
        "sparkline":              False,
        "price_change_percentage": "1h,24h,7d",
    }
    headers = {"Accept": "application/json"}
    resp = requests.get(API_URL, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def parse_api_response(raw_coins):
    """Convert raw API list into our standard row format."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    for c in raw_coins:
        price      = c.get("current_price")
        change_1h  = c.get("price_change_percentage_1h_in_currency")
        change_24h = c.get("price_change_percentage_24h_in_currency")
        change_7d  = c.get("price_change_percentage_7d_in_currency")
        mcap       = c.get("market_cap")
        vol        = c.get("total_volume")

        # Optional filters
        if PRICE_FILTER is not None and (price is None or price < PRICE_FILTER):
            continue
        if MIN_CHANGE is not None and (change_24h is None or change_24h < MIN_CHANGE):
            continue

        rows.append({
            "Timestamp":      ts,
            "Name":           c.get("name", ""),
            "Symbol":         c.get("symbol", "").upper(),
            "Price (USD)":    fmt_price(price),
            "1h Change (%)":  fmt_pct(change_1h),
            "24h Change (%)": fmt_pct(change_24h),
            "7d Change (%)":  fmt_pct(change_7d),
            "Market Cap":     fmt_large(mcap),
            "Volume (24h)":   fmt_large(vol),
        })
    return rows


# ── Fetch via Selenium + CoinMarketCap ──────────────────────────────────────

def fetch_via_selenium(top_n=TOP_N):
    """Scrape CoinMarketCap using Selenium (requires Chrome + chromedriver)."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager

    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )

    svc    = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=svc, options=opts)
    ts     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows   = []

    try:
        driver.get("https://coinmarketcap.com/")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
        )
        time.sleep(2)

        table_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in table_rows[:top_n]:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 7:
                continue
            rows.append({
                "Timestamp":      ts,
                "Name":           cols[2].text.split("\n")[0].strip(),
                "Symbol":         cols[2].text.split("\n")[1].strip() if "\n" in cols[2].text else "",
                "Price (USD)":    cols[3].text.strip(),
                "1h Change (%)":  cols[4].text.strip(),
                "24h Change (%)": cols[5].text.strip(),
                "7d Change (%)":  cols[6].text.strip(),
                "Market Cap":     cols[7].text.strip() if len(cols) > 7 else "",
                "Volume (24h)":   cols[8].text.strip() if len(cols) > 8 else "",
            })
    finally:
        driver.quit()

    return rows


# ── CSV I/O ─────────────────────────────────────────────────────────────────

def save_to_csv(rows, filepath=CSV_FILE):
    """Append rows to CSV, writing header only on first create."""
    if not rows:
        print("  ⚠  No data to save.")
        return

    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

    verb = "Appended" if file_exists else "Created"
    print(f"  ✓ {verb} {len(rows)} row(s) → {filepath}")


# ── Pretty printer ───────────────────────────────────────────────────────────

def print_table(rows):
    cols = ["Name", "Symbol", "Price (USD)", "24h Change (%)", "Market Cap"]
    widths = {c: max(len(c), max(len(r[c]) for r in rows)) for c in cols}
    sep = "  ".join("-" * widths[c] for c in cols)
    hdr = "  ".join(c.ljust(widths[c]) for c in cols)
    print("\n" + hdr)
    print(sep)
    for r in rows:
        print("  ".join(r[c].ljust(widths[c]) for c in cols))
    print()


# ── Entry point ──────────────────────────────────────────────────────────────

def run_once():
    print(f"\n[{datetime.now():%H:%M:%S}] Fetching top {TOP_N} coins …")
    try:
        if USE_SELENIUM:
            rows = fetch_via_selenium(TOP_N)
        else:
            raw  = fetch_via_api(TOP_N)
            rows = parse_api_response(raw)
    except Exception as e:
        print(f"  ✗ Fetch failed: {e}")
        return

    if rows:
        print_table(rows)
    save_to_csv(rows)


def main():
    parser = argparse.ArgumentParser(description="Crypto Price Tracker")
    parser.add_argument("--loop", type=int, default=0,
                        metavar="SECONDS",
                        help="Re-fetch every N seconds (0 = run once)")
    parser.add_argument("--top",  type=int, default=TOP_N,
                        help=f"Number of coins to fetch (default {TOP_N})")
    parser.add_argument("--output", default=CSV_FILE,
                        help=f"Output CSV path (default {CSV_FILE})")
    args = parser.parse_args()

    global TOP_N, CSV_FILE
    TOP_N    = args.top
    CSV_FILE = args.output

    print("=" * 52)
    print("  Cryptocurrency Price Tracker")
    print(f"  Mode    : {'Selenium/CMC' if USE_SELENIUM else 'API/CoinGecko'}")
    print(f"  Top     : {TOP_N} coins")
    print(f"  Output  : {CSV_FILE}")
    print(f"  Loop    : {args.loop}s" if args.loop else "  Loop    : once")
    print("=" * 52)

    if args.loop:
        while True:
            run_once()
            print(f"  ⏳ Next run in {args.loop}s … (Ctrl-C to stop)")
            time.sleep(args.loop)
    else:
        run_once()


if __name__ == "__main__":
    main()
