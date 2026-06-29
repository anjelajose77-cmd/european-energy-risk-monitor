# European Cross-Commodity Risk Monitor

A daily market-risk engine for a European energy book spanning **gas (TTF)**, **carbon (EUA)** and **German power**. It pulls live public price data, values a cross-commodity position book, and produces the standard morning risk pack a market-risk desk would circulate — P&L attribution, Value at Risk, stress tests, and position-limit alerts — exported to a structured Excel report with a single command.

> Built as a learning + portfolio project on free public data. The position book is illustrative (see [Caveats](#caveats)); the risk methodology is the same one used on a live desk.

---

## What it does

Running `python run_risk.py` executes the full daily workflow end to end:

- **Live cross-commodity data** — pulls daily price history for three independent feeds (TTF gas, EUA carbon, German day-ahead power) and aligns them on a shared calendar.
- **P&L attribution by leg** — breaks total mark-to-market P&L into each commodity's contribution, so you can see *where* the book's money comes from.
- **Value at Risk (1-day, 95%)** — computed two independent ways and cross-checked:
  - *Historical simulation* — replays the real distribution of past daily price moves against today's positions.
  - *Parametric (variance–covariance)* — `z × portfolio standard deviation`, assuming normally distributed moves.
- **Stress testing & scenario analysis** — applies four named scenarios (cold snap + supply disruption, demand destruction, carbon-policy tightening, mild winter / oversupply) and reports the P&L impact of each.
- **Position-limit breach alerts** — checks each leg's exposure against its limit, and total VaR against a VaR limit, flagging any breach.
- **Structured Excel report** — a formatted, five-tab workbook (`output/risk_report_YYYYMMDD.xlsx`) with breaches highlighted.

---

## Quick start

```bash
# 1. set up
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Mac/Linux
pip install -r requirements.txt

# 2. run the full daily risk workflow
python run_risk.py
```

The console prints a summary and saves the Excel report to `output/`.

---

## How it works

| File | Role |
|------|------|
| `positions.csv`   | The position book — one row per leg (direction, quantity, entry price) |
| `risk_data.py`    | Live data layer: pulls and aligns the three price feeds |
| `risk_engine.py`  | Risk calculations: P&L attribution, VaR (historical + parametric), stress/scenarios, limit checks |
| `excel_report.py` | Builds the formatted multi-tab Excel report |
| `run_risk.py`     | Orchestrator — runs everything and exports the report in one command |

Calculation and presentation are deliberately separated: `risk_engine.py` only computes numbers, `excel_report.py` only formats them.

---

## Data sources

| Leg | Source | Detail |
|-----|--------|--------|
| Gas — TTF front-month | Yahoo Finance (`yfinance`) | Dutch TTF gas futures (`TTF=F`) |
| Carbon — EU ETS (EUA) | Yahoo Finance (`yfinance`) | EUA carbon (`CO2.L`) |
| Power — German day-ahead | [energy-charts.info](https://www.energy-charts.info) API | DE-LU bidding zone, hourly prices averaged to daily |

All three are free, public, daily feeds. No paid market-data subscription required.

---

## Methodology notes

- **Timezone alignment.** Yahoo Finance stamps each feed in its own timezone, so naively concatenating the series leaves zero overlapping dates. Each timestamp is collapsed to a plain calendar date before aligning, which fixes the join.
- **Absolute price moves for VaR, not percentage returns.** German power is extremely volatile (day-to-day swings well over 100%). Percentage returns make parametric VaR explode, because a single outlier return dominates the variance. Using absolute price changes (`.diff()`) weighted by position size produces a realistic VaR that reconciles with the historical figure.

---

## Caveats

- The **position book is illustrative** — `positions.csv` and its entry prices are sample values, not real positions. The P&L magnitudes reflect those sample entries; the *methodology* is what matters.
- Prices are **daily closes / day-ahead**, so VaR is a 1-day measure. Intraday risk is out of scope.
- VaR's 95% confidence means the ~1-in-20 worst day can exceed it — it is not a worst-case number.
