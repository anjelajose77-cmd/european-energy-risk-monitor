import os
from datetime import date
from data_ingestion import get_all_metrics
from charts import generate_all_charts
from llm_brief import generate_brief
from report import generate_report


def run_monitor():
    print("=" * 55)
    print("  COBBLESTONE ENERGY - EUROPEAN CROSS-COMMODITY MONITOR")
    print(f"  {date.today().strftime('%A, %d %B %Y')}")
    print("=" * 55)

    print("\n PULLING MARKET DATA...")
    metrics = get_all_metrics()

    print("\n GENERATING CHARTS...")
    chart1, chart2, chart3, storage_deficit = generate_all_charts(metrics)

    print("\n GENERATING AI TRADING BRIEF...")
    brief = generate_brief(metrics)

    print("\n" + "=" * 55)
    print("  TODAY'S TRADING BRIEF")
    print("=" * 55)
    print(brief)

    print("\n" + "=" * 55)
    print("  OUTPUT FILES")
    print("=" * 55)
    print("  Chart 1 : output/chart1_ttf_history.png")
    print("  Chart 2 : output/chart2_storage_deficit.png")
    print("  Chart 3 : output/chart3_spark_spread.png")
    print("  LLM Log : output/llm_log.json")
    print("=" * 55)

    print("\n GENERATING PDF Report...")
    pdf_path = generate_report(metrics, brief, chart1, chart2, chart3, storage_deficit)
    print(f"  PDF saved: {pdf_path}")
    print("\nMonitor complete.")


if __name__ == "__main__":
    run_monitor()