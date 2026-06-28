from fpdf import FPDF
from datetime import date
import os
import math

OUTPUT_DIR = "output"

CE_TEAL = (0, 168, 143)
CE_DARK = (20, 30, 35)
CE_MID = (40, 55, 60)
CE_LIGHT = (235, 248, 245)
CE_ACCENT = (0, 200, 170)
CE_WHITE = (255, 255, 255)
CE_GREY = (100, 115, 120)


def clean(text):
    if text is None:
        return ""
    text = str(text)
    replacements = {
        "\u20ac": "EUR", "\u2014": "-", "\u2013": "-",
        "\u2192": "->", "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"', "\u2022": "*",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def is_nan(val):
    try:
        return math.isnan(float(val))
    except (TypeError, ValueError):
        return False


class TradingReport(FPDF):
    def header(self):
        self.set_fill_color(*CE_DARK)
        self.rect(0, 0, 210, 24, "F")
        self.set_fill_color(*CE_TEAL)
        self.rect(0, 22, 210, 2, "F")
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*CE_ACCENT)
        self.set_xy(10, 5)
        self.cell(100, 8, "COBBLESTONE ENERGY", align="L")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*CE_WHITE)
        self.set_xy(10, 13)
        self.cell(100, 6, "European Cross-Commodity Risk Monitor", align="L")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*CE_ACCENT)
        self.set_xy(130, 8)
        self.cell(70, 7, date.today().strftime("%d %B %Y"), align="R")
        self.ln(20)

    def footer(self):
        self.set_fill_color(*CE_DARK)
        self.rect(0, 284, 210, 14, "F")
        self.set_fill_color(*CE_TEAL)
        self.rect(0, 284, 210, 1.5, "F")
        self.set_y(-11)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*CE_ACCENT)
        self.cell(0, 8, f"Automated Daily Monitor  |  Anjela Jose  |  anjelajose22@gmail.com  |  Page {self.page_no()}", align="C")

    def section_title(self, title):
        self.set_fill_color(*CE_TEAL)
        self.rect(10, self.get_y(), 3, 8, "F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*CE_DARK)
        self.set_x(15)
        self.cell(0, 8, title, ln=True)
        self.ln(2)

    def teal_divider(self):
        self.set_fill_color(*CE_TEAL)
        self.rect(10, self.get_y(), 190, 0.8, "F")
        self.ln(4)

    def caption(self, text):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*CE_GREY)
        self.set_x(12)
        self.multi_cell(186, 5, clean(text))
        self.ln(2)


def metric_card(pdf, x, y, w, h, label, value, unit, ok):
    pdf.set_fill_color(210, 225, 220)
    pdf.rect(x + 1, y + 1, w, h, "F")
    pdf.set_fill_color(*CE_LIGHT)
    pdf.set_draw_color(*CE_TEAL)
    pdf.rect(x, y, w, h, "FD")
    r, g, b = CE_TEAL if ok else (200, 80, 50)
    pdf.set_fill_color(r, g, b)
    pdf.rect(x, y, w, 2.5, "F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*CE_GREY)
    pdf.set_xy(x + 1, y + 3.5)
    pdf.cell(w - 2, 4, clean(label), align="C")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*CE_DARK)
    pdf.set_xy(x + 1, y + 8)
    pdf.cell(w - 2, 7, clean(value), align="C")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*CE_GREY)
    pdf.set_xy(x + 1, y + 17)
    pdf.cell(w - 2, 4, clean(unit), align="C")
    dot_r, dot_g, dot_b = CE_TEAL if ok else (200, 80, 50)
    pdf.set_fill_color(dot_r, dot_g, dot_b)
    pdf.circle(x + w - 3, y + 3.5, 1.2, "F")


def generate_report(metrics, brief, chart1_path, chart2_path, chart3_path=None, storage_deficit=None):
    print("Generating PDF report...")

    
    if storage_deficit is not None:
        deficit_str = f"{storage_deficit}pp"
    else:
        deficit_str = "N/A pp"

    
    m_dict = {m["metric"]: m["value"] for m in metrics}
    eua_val = m_dict.get("EU ETS Carbon (EUA)")
    try:
        eua_carbon_cost = round(float(eua_val) * 0.202, 0)
        eua_display = f"At EUR {float(eua_val):.0f}/t, carbon adds ~EUR {eua_carbon_cost:.0f}/MWh on top of the gas cost."
    except (TypeError, ValueError):
        eua_display = "At EUR 75/t, carbon adds ~EUR 15/MWh on top of the gas cost."

    pdf = TradingReport()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()

   
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*CE_DARK)
    pdf.cell(0, 10, "Cross-Commodity Risk Pack", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*CE_TEAL)
    pdf.cell(0, 6, "Gas + Carbon  ->  Power Curve Implications  |  " + date.today().strftime("%d %B %Y"), ln=True)
    pdf.ln(2)
    pdf.teal_divider()

    
    pdf.section_title("Today's Monitor Metrics")
    card_w = 30
    card_h = 22
    gap = 2
    start_x = 12
    start_y = pdf.get_y()

    for i, m in enumerate(metrics):
        x = start_x + i * (card_w + gap)
        y = start_y
        val = m["value"]
        display = "N/A" if val is None or is_nan(val) else str(val)
        ok = m["status"] == "ok" and not (val is not None and is_nan(val))
        metric_card(pdf, x, y, card_w, card_h, m["metric"], display, m["unit"], ok)

    pdf.set_y(start_y + card_h + 5)
    pdf.teal_divider()


    pdf.section_title("AI-Generated Trading Brief")
    pdf.set_fill_color(*CE_LIGHT)
    pdf.set_draw_color(*CE_TEAL)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 55, 60)
    pdf.set_x(12)
    pdf.multi_cell(186, 5.5, clean(brief), border=1, fill=True)
    pdf.ln(3)
    pdf.teal_divider()


    pdf.section_title("TTF Natural Gas - 3 Month Price History")
    if chart1_path and os.path.exists(chart1_path):
        pdf.image(chart1_path, x=12, w=186)
    pdf.caption("TTF front-month is the marginal fuel cost signal for European power. Gas-fired plants set the clearing price across most hours of the day - a move in TTF flows directly and immediately into day-ahead and forward power prices. Traders use this chart to assess whether recent gas price moves represent a structural shift or a short-term sentiment trade.")
    pdf.teal_divider()


    pdf.section_title("EU Gas Storage: 2026 vs 2025 - Injection Season Deficit")
    if chart2_path and os.path.exists(chart2_path):
        pdf.image(chart2_path, x=12, w=186)
    pdf.caption("Storage fill rate versus the prior year is the key physical tightness indicator for the power curve. A deficit vs last year means less buffer against winter demand spikes - this tightens the supply/demand balance and supports higher forward power prices. Traders watch the year-on-year gap to assess whether current TTF levels are justified by fundamentals or driven by sentiment.")
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(*CE_GREY)
    pdf.set_x(12)
    pdf.cell(0, 5, "Note: GIE AGSI+ API data displayed to T-1 due to publication lag.", ln=True)
    pdf.ln(3)
    pdf.teal_divider()


    pdf.section_title("Gas-Fired Power: Generation Cost vs German DA Price")
    if chart3_path and os.path.exists(chart3_path):
        pdf.image(chart3_path, x=12, w=186)
    else:
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(*CE_GREY)
        pdf.set_x(12)
        pdf.cell(0, 10, "Chart unavailable - API timeout. Re-run to regenerate.", ln=True)
    pdf.caption("This chart shows the economics of gas-fired generation - the core driver of European power prices. The stacked areas represent total generation cost (gas + carbon); the red line is the actual clearing price (German DA). When DA exceeds total cost, the spark spread is positive and gas plants dispatch. When it falls below, gas is pushed out of the merit order. Traders use this to assess power curve risk: a persistently positive spread supports higher forwards; a negative spread signals renewable oversupply or demand weakness.")
    pdf.teal_divider()

    pdf.section_title("Metric Rationale & Methodology")
    rationale = [
        ("TTF Front-Month (EUR/MWh)",
         "The European gas benchmark. Gas-fired power plants set the marginal price of electricity across most hours in Europe. TTF is the primary input cost - every move flows directly into power curve pricing."),
        ("EU Gas Storage Fill (%)",
         f"The physical tightness signal. Storage fill vs the same date last year shows how much winter supply buffer Europe has. Currently {deficit_str} below 2025, meaning the market is more exposed to a cold snap or LNG disruption than the current TTF price implies."),
        ("EU ETS Carbon / EUA (EUR/tonne)",
         f"The carbon cost overlay. Each MWh of gas-fired generation emits ~0.202 tonnes of CO2, each requiring an EU Allowance. {eua_display} ETS reform in 2026 and CBAM implementation are structural tailwinds for EUA prices."),
        ("Clean Spark Spread (EUR/MWh)",
         "DERIVED METRIC - Formula: German Power DA - (TTF x 7.5/3.6) - (EUA x 0.202). Here 7.5 is the heat rate in GJ/MWh divided by 3.6 to convert to MWh, giving ~2.08 MWh gas per MWh power (~48% CCGT efficiency). 0.202 is the CO2 emission factor (t/MWh). Positive = gas plants profitable and dispatching. Negative = gas pushed out of merit order."),
        ("German Power DA (EUR/MWh)",
         "The spot power benchmark. Clears after all generation sources have bid in. The gap between DA and the forward curve (Cal-27 ~EUR 93/MWh) signals the market structural view on tightness over time."),
        ("EU LNG Send-Out (GWh/day)",
         "The flow signal. Europe is structurally dependent on LNG imports since 2022. Daily send-out is the fastest supply signal available - a drop due to geopolitical disruption or Asian demand competition translates to TTF upward pressure within days."),
    ]

    fill = False
    for metric, explanation in rationale:
        pdf.set_fill_color(*(CE_LIGHT if fill else CE_WHITE))
        pdf.set_x(12)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*CE_TEAL)
        pdf.cell(0, 6, clean(metric), fill=True, ln=True)
        pdf.set_x(12)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*CE_DARK)
        pdf.multi_cell(186, 5, clean(explanation), fill=True)
        pdf.ln(1)
        fill = not fill

    pdf.ln(3)
    pdf.teal_divider()


    pdf.section_title("Data Sources")
    sources = [
        ("TTF Front-Month",     "Yahoo Finance (TTF=F) via yfinance"),
        ("EU Gas Storage Fill", "GIE AGSI+ API (agsi.gie.eu) - T-1 lag"),
        ("EU ETS Carbon (EUA)", "Yahoo Finance (CO2.L) via yfinance - last available price"),
        ("Clean Spark Spread",  "Derived - see formula in metric rationale above"),
        ("German Power DA",     "Energy-Charts API (api.energy-charts.info)"),
        ("EU LNG Send-Out",     "GIE ALSI+ API (alsi.gie.eu)"),
        ("Trading Brief",       "LLM-generated via Groq API (llama-3.3-70b-versatile)"),
        ("Market Context",      "NewsAPI (newsapi.org) - live headlines auto-fetched daily"),
    ]
    fill = False
    for label, source in sources:
        pdf.set_fill_color(*(CE_LIGHT if fill else CE_WHITE))
        pdf.set_x(12)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*CE_TEAL)
        pdf.cell(50, 6, clean(label), fill=True, border="B")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*CE_DARK)
        pdf.cell(136, 6, clean(source), fill=True, border="B", ln=True)
        fill = not fill

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"output/cobblestone_monitor_{date.today().strftime('%Y%m%d')}.pdf"
    pdf.output(filename)
    print(f"  PDF saved: {filename}")
    return filename


if __name__ == "__main__":
    from data_ingestion import get_all_metrics
    from charts import generate_all_charts
    from llm_brief import generate_brief

    metrics = get_all_metrics()
    chart1, chart2, chart3, storage_deficit = generate_all_charts(metrics)
    brief = generate_brief(metrics)
    generate_report(metrics, brief, chart1, chart2, chart3, storage_deficit)
    print("Done!")