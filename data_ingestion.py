import os
from dotenv import load_dotenv
load_dotenv()

import yfinance as yf
import requests
import pandas as pd
import math
from datetime import date, timedelta


def get_ttf_price():
    """Metric 1: TTF front-month gas price"""
    try:
        ttf = yf.Ticker("TTF=F")
        hist = ttf.history(period="5d")
        hist = hist.dropna(subset=["Close"])
        price = round(hist["Close"].iloc[-1], 2)
        return {"metric": "TTF Front-Month", "value": price, "unit": "EUR/MWh", "status": "ok"}
    except Exception as e:
        return {"metric": "TTF Front-Month", "value": None, "unit": "EUR/MWh", "status": f"error: {e}"}


def get_carbon_price():
    """Metric 3: EU ETS carbon price via Yahoo Finance - uses 5d to handle weekends"""
    try:
        eua = yf.Ticker("CO2.L")
        hist = eua.history(period="5d")
        hist = hist.dropna(subset=["Close"])
        price = round(hist["Close"].iloc[-1], 2)
        return {"metric": "EU ETS Carbon (EUA)", "value": price, "unit": "EUR/tonne", "status": "ok"}
    except Exception as e:
        return {"metric": "EU ETS Carbon (EUA)", "value": None, "unit": "EUR/tonne", "status": f"error: {e}"}


def get_german_power():
    """Metric 5: German day-ahead power via Energy-Charts API"""
    try:
        today = str(date.today())
        url = "https://api.energy-charts.info/price"
        params = {"bzn": "DE-LU", "start": today, "end": today}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        prices = [p for p in data["price"] if p is not None]
        if not prices:
            raise ValueError("No price data returned")
        avg_price = round(sum(prices) / len(prices), 2)
        return {"metric": "German Power DA", "value": avg_price, "unit": "EUR/MWh", "status": "ok"}
    except Exception as e:
        return {"metric": "German Power DA", "value": 88.0, "unit": "EUR/MWh", "status": f"fallback: {e}"}


def get_gas_storage():
    """Metric 2: EU gas storage fill % via GIE AGSI API"""
    try:
        api_key = os.getenv("GIE_API_KEY")
        url = "https://agsi.gie.eu/api"
        params = {"country": "eu", "size": 1, "date": str(date.today() - timedelta(days=1))}
        headers = {"x-key": api_key}
        r = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()
        fill = round(float(data["data"][0]["full"]), 2)
        return {"metric": "EU Gas Storage Fill", "value": fill, "unit": "%", "status": "ok"}
    except Exception as e:
        return {"metric": "EU Gas Storage Fill", "value": 45.3, "unit": "%", "status": f"fallback: {e}"}


def get_clean_spark_spread(ttf, carbon, power):
    """Metric 4: Clean spark spread (derived)"""
    try:
        heat_rate = 7.5
        emission_factor = 0.202
        gas_cost = ttf * heat_rate / 3.6
        carbon_cost = carbon * emission_factor
        spread = round(power - gas_cost - carbon_cost, 2)
        return {"metric": "Clean Spark Spread", "value": spread, "unit": "EUR/MWh", "status": "ok"}
    except Exception as e:
        return {"metric": "Clean Spark Spread", "value": None, "unit": "EUR/MWh", "status": f"error: {e}"}


def get_lng_sendout():
    """Metric 6: EU LNG send-out (GWh/day) via GIE ALSI API"""
    try:
        api_key = os.getenv("GIE_API_KEY")
        headers = {"x-key": api_key}
        country_codes = ["eu", "EU", "99EU"]
        dates_to_try = [str(date.today() - timedelta(days=i)) for i in range(1, 4)]

        for country in country_codes:
            for gas_date in dates_to_try:
                url = "https://alsi.gie.eu/api"
                params = {"country": country, "size": 1, "date": gas_date}
                r = requests.get(url, params=params, headers=headers, timeout=15)
                data = r.json()
                print(f"  Trying country={country} date={gas_date}: total={data.get('total')}")
                if data.get("data"):
                    sendout = round(float(data["data"][0]["sendOut"]), 1)
                    return {"metric": "EU LNG Send-Out", "value": sendout, "unit": "GWh/day", "status": "ok"}

        return {"metric": "EU LNG Send-Out", "value": None, "unit": "GWh/day", "status": "no data found"}

    except Exception as e:
        return {"metric": "EU LNG Send-Out", "value": None, "unit": "GWh/day", "status": f"error: {e}"}


def get_all_metrics():
    print("Pulling all metrics...")
    ttf_data = get_ttf_price()
    carbon_data = get_carbon_price()
    power_data = get_german_power()
    storage_data = get_gas_storage()

    ttf_val = ttf_data["value"] if ttf_data["value"] is not None and not math.isnan(float(ttf_data["value"])) else 41.5
    carbon_val = carbon_data["value"] if carbon_data["value"] is not None and not math.isnan(float(carbon_data["value"])) else 75.0
    power_val = power_data["value"] if power_data["value"] is not None and not math.isnan(float(power_data["value"])) else 90.0

    spark_data = get_clean_spark_spread(ttf_val, carbon_val, power_val)
    lng_data = get_lng_sendout()

    metrics = [ttf_data, storage_data, carbon_data, spark_data, power_data, lng_data]

    print("\n--- TODAY'S METRICS ---")
    for m in metrics:
        print(f"{m['metric']:<25} {str(m['value']):<10} {m['unit']:<10} [{m['status']}]")
    return metrics


if __name__ == "__main__":
    get_all_metrics()