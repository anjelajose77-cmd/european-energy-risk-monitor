import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import requests
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from collections import defaultdict
import os
from dotenv import load_dotenv
load_dotenv()

OUTPUT_DIR = "output"


def chart_ttf_history():
    """Chart 1: TTF gas price - last 3 months"""
    print("Generating Chart 1: TTF price history...")
    try:
        ttf = yf.Ticker("TTF=F")
        hist = ttf.history(period="3mo")
        hist.index = hist.index.tz_localize(None)

        fig, ax = plt.subplots(figsize=(12, 5))
        fig.patch.set_facecolor("#0d1117")
        ax.set_facecolor("#0d1117")

        high_3m = round(hist["Close"].max(), 2)
        low_3m = round(hist["Close"].min(), 2)
        today_price = round(hist["Close"].iloc[-1], 2)
        yday_price = round(hist["Close"].iloc[-2], 2)
        pct_change = round((today_price - yday_price) / yday_price * 100, 2)
        change_sign = "+" if pct_change > 0 else ""

        ax.plot(hist.index, hist["Close"], color="#00d4aa", linewidth=2,
                label=f"TTF  |  Today: {today_price}  |  {change_sign}{pct_change}% vs yday  |  3M High: {high_3m}  |  3M Low: {low_3m}")
        ax.fill_between(hist.index, hist["Close"], alpha=0.15, color="#00d4aa")

        ax.set_title("TTF Natural Gas - 3 Month Price History", color="white", fontsize=14, pad=15)
        ax.set_ylabel("EUR/MWh", color="white")
        ax.spines["bottom"].set_color("white")
        ax.spines["left"].set_color("white")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.label.set_color("white")
        ax.xaxis.label.set_color("white")
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        plt.setp(ax.get_xticklabels(), color='white')
        plt.setp(ax.get_yticklabels(), color='white')

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=45, ha="right")

        ax.legend(facecolor="#1a1a2e", labelcolor="white", fontsize=8)
        ax.set_xlim(left=hist.index[0], right=hist.index[-1] + pd.Timedelta(days=5))
        plt.tight_layout()

        path = os.path.join(OUTPUT_DIR, "chart1_ttf_history.png")
        plt.savefig(path, dpi=150, facecolor="#0d1117")
        plt.close()
        print(f"  Saved: {path}")
        return path

    except Exception as e:
        print(f"  Chart 1 error: {e}")
        return None


def chart_storage_vs_lastyear(metrics=None):
    """Chart 2: EU gas storage this year vs last year"""
    print("Generating Chart 2: Storage deficit chart...")
    try:
        api_key = os.getenv("GIE_API_KEY")
        headers = {"x-key": api_key}

        storage_this_year = {} 
        today = date.today()


        base = today - timedelta(days=2)
        for weeks_ago in range(26, 0, -1):
            d = base - timedelta(weeks=weeks_ago)
            try:
                r = requests.get(
                    "https://agsi.gie.eu/api",
                    params={"country": "eu", "size": 1, "date": str(d)},
                    headers=headers, timeout=8
                )
                data = r.json()
                if data.get("data"):
                    storage_this_year[d] = float(data["data"][0]["full"])
            except:
                pass


        for days_ago in range(7, 0, -1):
            d = today - timedelta(days=days_ago)
            if d not in storage_this_year:
                try:
                    r = requests.get(
                        "https://agsi.gie.eu/api",
                        params={"country": "eu", "size": 1, "date": str(d)},
                        headers=headers, timeout=8
                    )
                    data = r.json()
                    if data.get("data"):
                        storage_this_year[d] = float(data["data"][0]["full"])
                except:
                    pass

        
        combined = sorted(storage_this_year.items())
        dates_this_year = [x[0] for x in combined]
        fills_this_year = [x[1] for x in combined]

        print(f"  Data points this year: {len(fills_this_year)}")

        
        dates_last_year = []
        fills_last_year = []
        for d in dates_this_year:
            d_ly = d - timedelta(days=365)
            try:
                r = requests.get(
                    "https://agsi.gie.eu/api",
                    params={"country": "eu", "size": 1, "date": str(d_ly)},
                    headers=headers, timeout=8
                )
                data = r.json()
                if data.get("data"):
                    fill = float(data["data"][0]["full"])
                    dates_last_year.append(d)
                    fills_last_year.append(fill)
            except:
                pass

        print(f"  Data points last year: {len(fills_last_year)}")

        if not fills_this_year or not fills_last_year:
            print("  No data returned - check GIE_API_KEY in .env")
            return None, None

        BG = "#0a0e1a"
        COL_2026 = "#00d4aa"
        COL_2025 = "#c0c0c0"
        COL_TARGET = "#ff4444"

        fig, ax = plt.subplots(figsize=(12, 5))
        fig.patch.set_facecolor(BG)
        ax.set_facecolor(BG)

        min_len = min(len(fills_this_year), len(fills_last_year))

        current_deficit = round(fills_last_year[min_len - 1] - fills_this_year[min_len - 1], 1)

        if metrics:
            m_dict = {m["metric"]: m["value"] for m in metrics}
            live_storage = m_dict.get("EU Gas Storage Fill") or fills_this_year[-1]
        else:
            live_storage = fills_this_year[-1]

        ax.plot(dates_this_year, fills_this_year, color=COL_2026,
                linewidth=2.5,
                label=f"2026 (this year)  |  current: {float(live_storage):.1f}%",
                zorder=3)
        ax.plot(dates_last_year, fills_last_year, color=COL_2025,
                linewidth=2.0, linestyle="--",
                label=f"2025 (last year)  |  current: {fills_last_year[-1]:.1f}%",
                zorder=2)

        ax.fill_between(
            dates_this_year[:min_len],
            fills_this_year[:min_len],
            fills_last_year[:min_len],
            alpha=0.35, color=COL_2026,
            label=f"Storage deficit  |  {current_deficit}pp below 2025"
        )

        ax.axhline(y=80, color=COL_TARGET, linewidth=1.2,
                   linestyle=":", label="EU 80% winter target")

        ax.set_title("EU Gas Storage: 2026 vs 2025 - Injection Season Deficit",
                     color="white", fontsize=14, pad=15)
        ax.set_ylabel("Storage Fill (%)", color="white")
        ax.set_ylim(0, 105)
        ax.spines["bottom"].set_color("#444455")
        ax.spines["left"].set_color("#444455")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        plt.setp(ax.get_xticklabels(), color='white')
        plt.setp(ax.get_yticklabels(), color='white')
        ax.yaxis.label.set_color("white")

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=3))
        plt.xticks(rotation=45, ha="right")

        ax.legend(facecolor="#1a1a2e", labelcolor="white", fontsize=9)
        plt.tight_layout()

        path = os.path.join(OUTPUT_DIR, "chart2_storage_deficit.png")
        plt.savefig(path, dpi=150, facecolor="#0d1117")
        plt.close()
        print(f"  Saved: {path}")
        return path, current_deficit

    except Exception as e:
        print(f"  Chart 2 error: {e}")
        return None, None


def chart_spark_spread(metrics=None):
    """Chart 3: Generation cost breakdown vs German DA power price"""
    print("Generating Chart 3: Spark spread vs German DA...")
    try:
        ttf = yf.Ticker("TTF=F")
        ttf_hist = ttf.history(period="3mo")
        ttf_hist.index = ttf_hist.index.tz_localize(None)

        eua = yf.Ticker("CO2.L")
        eua_hist = eua.history(period="3mo")
        eua_hist = eua_hist.dropna(subset=["Close"])
        eua_hist.index = eua_hist.index.tz_localize(None)

        common_dates = ttf_hist.index.intersection(eua_hist.index)
        ttf_prices = ttf_hist.loc[common_dates, "Close"].ffill().dropna()
        eua_prices = eua_hist.loc[common_dates, "Close"].ffill().dropna()
        common_dates = ttf_prices.index.intersection(eua_prices.index)
        ttf_prices = ttf_prices.loc[common_dates]
        eua_prices = eua_prices.loc[common_dates]

        heat_rate = 7.5
        emission_factor = 0.202
        gas_cost = ttf_prices * heat_rate / 3.6
        carbon_cost = eua_prices * emission_factor
        total_cost = gas_cost + carbon_cost

        today_ts = pd.Timestamp(date.today()).normalize()
        start_date = common_dates[0].strftime("%Y-%m-%d")
        end_date = common_dates[-1].strftime("%Y-%m-%d")
        r = requests.get(
            "https://api.energy-charts.info/price",
            params={"bzn": "DE-LU", "start": start_date, "end": end_date},
            timeout=30
        )
        price_data = r.json()

        daily_prices = defaultdict(list)
        for ts, p in zip(price_data.get("unix_seconds", []), price_data.get("price", [])):
            if p is not None:
                dt = pd.Timestamp(ts, unit="s")
                day = dt.normalize()
                if day < today_ts:
                    daily_prices[day].append(p)

        da_series = pd.Series({
            d: round(sum(prices) / len(prices), 2)
            for d, prices in daily_prices.items()
        }).sort_index()

        if metrics:
            m_dict = {m["metric"]: m["value"] for m in metrics}
            live_da = m_dict.get("German Power DA")
            if live_da is not None:
                da_series[today_ts] = float(live_da)
                da_series = da_series.sort_index()

        all_common = total_cost.index.intersection(da_series.index)
        gas_aligned = gas_cost.loc[all_common]
        carbon_aligned = carbon_cost.loc[all_common]
        total_aligned = total_cost.loc[all_common]
        da_aligned = da_series.loc[all_common]


        if metrics and today_ts not in all_common:
            m_dict = {m["metric"]: m["value"] for m in metrics}
            live_ttf = m_dict.get("TTF Front-Month")
            live_eua = m_dict.get("EU ETS Carbon (EUA)")
            live_da = m_dict.get("German Power DA")
            if live_ttf and live_da:
                live_eua_v = float(live_eua) if live_eua else 75.0
                live_gas = float(live_ttf) * 7.5 / 3.6
                live_carbon = live_eua_v * 0.202
                live_total = live_gas + live_carbon
                gas_aligned = pd.concat([gas_aligned, pd.Series([live_gas], index=[today_ts])]).sort_index()
                carbon_aligned = pd.concat([carbon_aligned, pd.Series([live_carbon], index=[today_ts])]).sort_index()
                total_aligned = pd.concat([total_aligned, pd.Series([live_total], index=[today_ts])]).sort_index()
                da_aligned = pd.concat([da_aligned, pd.Series([float(live_da)], index=[today_ts])]).sort_index()

        fig, ax = plt.subplots(figsize=(12, 5))
        fig.patch.set_facecolor("#0d1117")
        ax.set_facecolor("#0d1117")

        ax.fill_between(da_aligned.index, 0, gas_aligned.reindex(da_aligned.index).ffill(),
                        alpha=0.5, color="#4ecdc4",
                        label="Gas cost (TTF x 7.5/3.6)")
        ax.fill_between(da_aligned.index,
                        gas_aligned.reindex(da_aligned.index).ffill(),
                        total_aligned.reindex(da_aligned.index).ffill(),
                        alpha=0.5, color="#f7dc6f",
                        label="Carbon cost (EUA x 0.202)")
        ax.plot(da_aligned.index, da_aligned, color="#ff4444",
                linewidth=2, label="German Power DA (daily avg)", zorder=4)
        ax.plot(da_aligned.index, total_aligned.reindex(da_aligned.index).ffill(),
                color="white", linewidth=1.5, linestyle="--",
                label="Total generation cost", zorder=3)

        if metrics:
            m_dict = {m["metric"]: m["value"] for m in metrics}
            ttf_raw = m_dict.get("TTF Front-Month")
            eua_raw = m_dict.get("EU ETS Carbon (EUA)")
            pwr_raw = m_dict.get("German Power DA")
            spark_raw = m_dict.get("Clean Spark Spread")

            ttf_v = float(ttf_raw) if ttf_raw is not None else 0
            eua_v = float(eua_raw) if eua_raw is not None else 75.0
            pwr_v = float(pwr_raw) if pwr_raw is not None else 0

            g = round(ttf_v * 7.5 / 3.6, 1)
            c = round(eua_v * 0.202, 1)
            t = round(g + c, 1)

            s = round(float(spark_raw), 1) if spark_raw is not None else round(pwr_v - t, 1)
            sign = "+" if s > 0 else ""

            textstr = (f"Today (live):\n"
                       f"Gas cost:     EUR {g}/MWh\n"
                       f"Carbon cost:  EUR {c}/MWh\n"
                       f"Break-even:   EUR {t}/MWh\n"
                       f"German DA:    EUR {pwr_v}/MWh\n"
                       f"Spark spread: {sign}{s} EUR/MWh")
        else:
            def safe_round(val):
                try:
                    v = float(val)
                    return "N/A" if pd.isna(v) else round(v, 1)
                except:
                    return "N/A"
            g = safe_round(gas_aligned.ffill().iloc[-1])
            c = safe_round(carbon_aligned.ffill().iloc[-1])
            t = safe_round(total_aligned.ffill().iloc[-1])
            p = safe_round(da_aligned.iloc[-1])
            spark_fallback = da_aligned - total_aligned
            s = safe_round(spark_fallback.ffill().iloc[-1])
            sign = "+" if isinstance(s, float) and s > 0 else ""
            textstr = (f"Today:\n"
                       f"Gas cost:     EUR {g}/MWh\n"
                       f"Carbon cost:  EUR {c}/MWh\n"
                       f"Break-even:   EUR {t}/MWh\n"
                       f"German DA:    EUR {p}/MWh\n"
                       f"Spark spread: {sign}{s} EUR/MWh")

        props = dict(boxstyle='round', facecolor='#1a1a2e', alpha=0.9)
        ax.text(0.98, 0.05, textstr, transform=ax.transAxes,
                fontsize=8, color='white',
                verticalalignment='bottom', horizontalalignment='right', bbox=props)

        ax.set_title("Gas-Fired Power: Generation Cost vs German DA Price",
                     color="white", fontsize=13, pad=15)
        ax.set_ylabel("EUR/MWh", color="white")
        ax.spines["bottom"].set_color("#444")
        ax.spines["left"].set_color("#444")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        plt.setp(ax.get_xticklabels(), color='white')
        plt.setp(ax.get_yticklabels(), color='white')
        ax.yaxis.label.set_color("white")

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.xticks(rotation=45, ha="right")

        ax.legend(facecolor="#1a1a2e", labelcolor="white", fontsize=8,
                  loc="upper center", bbox_to_anchor=(0.5, -0.18),
                  ncol=4, borderaxespad=0)
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.25)

        path = os.path.join(OUTPUT_DIR, "chart3_spark_spread.png")
        plt.savefig(path, dpi=150, facecolor="#0d1117")
        plt.close()
        print(f"  Saved: {path}")
        return path

    except Exception as e:
        print(f"  Chart 3 error: {e}")
        return None


def generate_all_charts(metrics):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    chart1 = chart_ttf_history()
    chart2, storage_deficit = chart_storage_vs_lastyear(metrics)  
    chart3 = chart_spark_spread(metrics)
    return chart1, chart2, chart3, storage_deficit  


if __name__ == "__main__":
    generate_all_charts([])
    print("\nDone! Check your output/ folder for the charts.")