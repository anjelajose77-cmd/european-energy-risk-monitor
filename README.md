# European Cross-Commodity Monitor
### Cobblestone Energy — Case Study Submission
**Anjela Jose** | anjelajose22@gmail.com

**Full version with risk engine (VaR, stress testing, Excel reporting):** https://github.com/anjelajose77-cmd/european-energy-risk-monitor

## Overview
An automated daily monitor that converts public European gas and carbon market fundamentals into a trading narrative for the power curve. Runs end-to-end with a single command, producing a branded PDF brief with live metrics, charts, and an AI-generated trading narrative.

## What It Does
1. Pulls 6 live market metrics from public APIs
2. Generates 3 charts (TTF price history + EU storage deficit vs last year + Generation cost breakdown vs German DA power price)
3. Calls Groq LLM API to write a 150-200 word trading brief grounded in live data
4. Outputs a 3-page branded PDF report

## Setup

### 1. Clone the repo
```powershell
git clone https://github.com/anjelajose77-cmd/cobblestone-monitor.git
cd cobblestone-monitor
```

### 2. Create virtual environment
```powershell
python -m venv venv
venv\Scripts\activate        
source venv/bin/activate     
```

### 3. Install dependencies
```powershell
pip install pandas yfinance requests matplotlib fpdf2 groq python-dotenv
```

### 4. Set up API keys
Create a `.env` file in the root folder:
GIE_API_KEY=your_gie_key_here
GROQ_API_KEY=your_groq_key_here
NEWS_API_KEY=your_newsapi_key_here

**Where to get free API keys:**
- **GIE** (gas storage + LNG data): Register at agsi.gie.eu — select "Both ALSI and AGSI+" when registering
- **Groq** (LLM): Free at console.groq.com — no need to buy credits
- **NewsAPI** (live headlines): Free at newsapi.org

### 5. Run
```powershell
python main.py
```
## Output
All files saved to `output/` folder:
- `cobblestone_monitor_YYYYMMDD.pdf` — full branded report
- `chart1_ttf_history.png` — TTF 3-month price history
- `chart2_storage_deficit.png` — EU storage 2026 vs 2025
- `llm_log.json` — logged prompt and LLM output

## Monitor Metrics

| Metric | Source | Why It Matters |
|---|---|---|
| TTF Front-Month | Yahoo Finance | European gas benchmark — sets marginal cost of gas-fired power |
| EU Gas Storage Fill | GIE AGSI+ API | Physical tightness proxy — currently below 2025 levels |
| EU ETS Carbon (EUA) | Yahoo Finance | Carbon cost per MWh — structurally supported by 2026 ETS reform |
| Clean Spark Spread | Derived | Gas plant profitability — positive = gas units dispatched |
| German Power DA | Energy-Charts API | Spot power benchmark — daily reality check vs forward positions |
| EU LNG Send-Out | GIE ALSI+ API | Supply flow signal — critical given Hormuz disruption in 2026 |


## Files
main.py

 data_ingestion.py   — pulls all 6 metrics from public APIs
 charts.py           — generates TTF history + storage deficit charts
 llm_brief.py        — fetches live news context + calls Groq LLM
 report.py           — assembles 2-page branded PDF


## AI / LLM Integration
The LLM workflow in `llm_brief.py`:
1. Fetches today's energy headlines via NewsAPI
2. Injects live metrics + headlines into a structured prompt
3. Calls Groq API (llama-3.3-70b-versatile) to generate a 150-200 word trading brief
4. Logs the full prompt and output to `output/llm_log.json`

This eliminates manual morning brief writing — analyst reviews and approves rather than drafts from scratch.
