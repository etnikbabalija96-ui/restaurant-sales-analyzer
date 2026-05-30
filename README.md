# Restaurant Sales Analyzer

Upload a CSV of restaurant sales data. Get business insights and AI-powered recommendations in your terminal.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-24%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

```
╭─────────────────────────────────────╮
│ Restaurant Sales Analyzer           │
│ Business intelligence from your CSV │
╰─────────────────────────────────────╯

✓ Loaded 55 rows
✓ Analysis complete

── Sales Overview ──────────────────────────────
  Total Revenue:   $3,152.09
  Total Orders:    55
  Avg Line Value:  $57.31
  Date Range:      2024-01-01 to 2024-01-14

── Top Items by Revenue ────────────────────────
  🥇 Margherita Pizza    $419.72
  🥈 BBQ Burger          $293.79
  🥉 Pepperoni Pizza     $287.82

── Revenue by Day ──────────────────────────────
  Saturday   $1,037.16  ████████████████████ ← best
  Sunday       $519.54  ████████████
  Monday       $248.77  ████ ← slowest

── AI Recommendations ──────────────────────────
  1. Double down on Saturday dinner service...
  2. Consider dropping Onion Rings ($16.47)...
```

## What it does

- **Parses any sales CSV** — auto-detects columns, handles messy headers
- **Revenue analysis** — total, daily average, per-item breakdown
- **Category breakdown** — revenue share by food category with visual bars
- **Day-of-week patterns** — spot your peak and slow days
- **Server performance** — who's selling the most and at what average
- **Underperformer detection** — items that might be costing more than they earn
- **AI recommendations** — Claude reads your actual numbers and gives 5 specific, actionable business insights

## Quickstart

```bash
git clone https://github.com/YOUR_USERNAME/restaurant-sales-analyzer
cd restaurant-sales-analyzer
pip install -r requirements.txt
cp .env.example .env          # then add your Anthropic API key
python main.py data/sample_sales.csv
```

To run without an API key (skips AI section):
```bash
python main.py data/sample_sales.csv --no-ai
```

## CSV Format

Your CSV must have these columns (column names are case-insensitive):

| Column | Required | Description |
|--------|----------|-------------|
| `date` | ✅ | Any parseable date format |
| `item` | ✅ | Item name |
| `quantity` | ✅ | Number sold |
| `unit_price` | ✅ | Price per unit |
| `category` | optional | Food category (e.g. Pizza, Drinks) |
| `server` | optional | Staff member name |
| `day_of_week` | optional | Monday–Sunday |
| `time_of_day` | optional | Lunch / Dinner / Brunch etc. |

A sample CSV is included at `data/sample_sales.csv`.

## Usage

```bash
# Basic analysis with AI recommendations
python main.py your_data.csv

# Skip AI (no API key needed)
python main.py your_data.csv --no-ai

# Save report to file
python main.py your_data.csv --output report.txt

# Help
python main.py --help
```

## Setup

**1. Clone and install**
```bash
pip install -r requirements.txt
```

**2. Set your API key** (only needed for AI recommendations)
```bash
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...
```
Get a key at [console.anthropic.com](https://console.anthropic.com).

## Running Tests

```bash
python -m pytest tests/ -v
```

24 tests covering CSV loading, revenue calculation, category analysis, server stats, edge cases, and serialization.

## Project Structure

```
restaurant-sales-analyzer/
├── main.py                    # CLI entry point
├── analysis/
│   ├── analyzer.py            # Data loading and analysis engine
│   └── ai_recommendations.py  # Claude API integration
├── tests/
│   └── test_analyzer.py       # 24 tests
├── data/
│   └── sample_sales.csv       # Sample data to try it out
├── requirements.txt
└── .env.example
```

## Requirements

- Python 3.10+
- Anthropic API key (optional — only for the AI recommendations section)

## License

MIT
