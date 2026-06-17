# 🪙 Cryptocurrency Price Tracker

A Python tool that fetches **real-time cryptocurrency prices** from CoinGecko's free API and saves them to a timestamped CSV file for analysis, dashboards, or portfolio tracking.

Optionally upgrades to **Selenium + CoinMarketCap** scraping for JavaScript-rendered pages (flip one flag).

---

## Features

| Feature | Detail |
|---|---|
| Live data | Top 10 coins by market cap, refreshed on demand |
| CSV logging | Appends timestamped rows — enables trend tracking over time |
| Loop mode | Re-fetch every N seconds with `--loop 60` |
| Analysis script | Instant summary: best/worst performers, price history min/max/avg |
| Selenium mode | One-flag switch to scrape CoinMarketCap directly |
| Filters | Skip coins below a price threshold or 24 h change target |

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/crypto-price-tracker.git
cd crypto-price-tracker

# 2. Install dependencies
pip install -r requirements.txt

# 3. Fetch once
python scraper.py

# 4. Fetch every 5 minutes (Ctrl-C to stop)
python scraper.py --loop 300

# 5. Analyse the collected data
python analyze.py
```

---

## Project structure

```
crypto-price-tracker/
├── scraper.py          ← main script (API or Selenium)
├── analyze.py          ← CSV analysis & summary
├── crypto_prices.csv   ← auto-generated output
├── requirements.txt
└── README.md
```

---

## CLI options

### scraper.py

| Flag | Default | Description |
|---|---|---|
| `--loop N` | `0` (once) | Re-fetch every N seconds |
| `--top N`  | `10` | Number of coins to fetch |
| `--output` | `crypto_prices.csv` | CSV output path |

### analyze.py

| Flag | Default | Description |
|---|---|---|
| `--file` | `crypto_prices.csv` | CSV file to analyse |

---

## CSV columns

| Column | Example |
|---|---|
| Timestamp | `2026-06-16 10:30:00` |
| Name | `Bitcoin` |
| Symbol | `BTC` |
| Price (USD) | `$67,200.15` |
| 1h Change (%) | `+0.42%` |
| 24h Change (%) | `-1.30%` |
| 7d Change (%) | `+5.17%` |
| Market Cap | `$1.32T` |
| Volume (24h) | `$28.40B` |

---

## Switching to Selenium mode

Open `scraper.py` and set:

```python
USE_SELENIUM = True
```

Then install the extra deps:

```bash
pip install selenium webdriver-manager
```

Chrome must be installed on your machine. `webdriver-manager` handles ChromeDriver automatically.

---

## Optional filters

In `scraper.py`, uncomment and set:

```python
PRICE_FILTER = 1.0    # only coins priced above $1
MIN_CHANGE   = 2.0    # only coins with 24h change > +2%
```

---

## Technologies

- **Python 3.10+**
- `requests` — REST API calls
- `pandas` — data manipulation
- `selenium` + `webdriver-manager` — dynamic page scraping (optional)
- CoinGecko free public API (no key required)

---

## License

MIT
