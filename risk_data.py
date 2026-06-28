import yfinance as yf
import pandas as pd
import requests
from datetime import date, timedelta

LEGS=["Gas","Carbon","Power"]

def _fetch_yahoo(ticker):
    series=yf.Ticker(ticker).history(period="6mo")["Close"]
    series.index=pd.to_datetime(series.index.date)
    return series

def _fetch_power():
    end=date.today()
    start=end-timedelta(days=180)
    url="https://api.energy-charts.info/price"
    params={"bzn":"DE-LU", "start":str(start),"end":str(end)}

    data=requests.get(url, params=params, timeout=30).json()
    power = pd.DataFrame({
        "timestamp": pd.to_datetime(data["unix_seconds"], unit="s"),
        "price": data["price"],
    }).dropna(subset=["price"])
    power["date"] = power["timestamp"].dt.date
    daily = power.groupby("date")["price"].mean()
    daily.index = pd.to_datetime(daily.index)
    return daily

def get_price_history():
    print("Loading market history")
    gas=_fetch_yahoo("TTF=F")
    carbon= _fetch_yahoo("CO2.L")
    power=_fetch_power()
    prices=pd.concat([gas, carbon ,power], axis=1, sort=False)
    prices.columns= LEGS
    prices=prices.dropna()
    print(f"Aligned history: {len(prices)} days, all metrics live")
    return prices

if __name__=="__main__":
    history=get_price_history()
    print("\nMonst recent 5 days (EUR/MWh):")
    print(history.tail().round(2))