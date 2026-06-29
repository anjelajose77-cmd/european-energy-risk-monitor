import pandas as pd
import numpy as np
from risk_data import get_price_history

def load_positions(path="positions.csv"):
    pos=pd.read_csv(path)
    pos["sign"] =[1 if d=="long"else -1 for d in pos["direction"]]
    pos["signed_qty"] = pos["quantity"]*pos["sign"]
    return pos

def pnl_by_leg(pos, latest_prices):
    """P&L per leg = signed quantity * (today's price - entry price)."""
    pos = pos.copy()
    pos["current_price"] = pos["leg"].map(latest_prices)
    pos["pnl"] = pos["signed_qty"] * (pos["current_price"] - pos["entry_price"])
    return pos

def historical_var(history, book, confidence = 0.95):
    moves= history.diff().dropna()
    qty={row.leg: row.signed_qty for row in book.itertuples()}
    weights= np.array([qty[leg] for leg in moves.columns])
    daily_pnl= moves.values @ weights
    var= -np.percentile(daily_pnl, (1-confidence)*100)
    return round(var,0)

def parametric_var(history, book, confidence=0.95):
    moves = history.diff().dropna()
    qty={row.leg:row.signed_qty for row in book.itertuples()}
    weights=np.array([qty[leg] for leg in moves.columns])
    cov= moves.cov().values
    portfolio_std=np.sqrt(weights @ cov @ weights)
    z={0.90:1.282, 0.95:1.645, 0.99: 2.326}. get(confidence, 1.645)
    return round(z* portfolio_std,0)


SCENARIOS={"Cold snap + supply disruption": {"Gas": 0.35, "Power": 0.30, "Carbon": 0.05},
    "Demand destruction (recession)": {"Gas": -0.25, "Power": -0.20, "Carbon": -0.15},
    "Carbon policy tightening":       {"Gas": 0.05, "Power": 0.10, "Carbon": 0.40},
    "Mild winter / oversupply":       {"Gas": -0.20, "Power": -0.15, "Carbon": -0.05}}

def stress_test(book,shocks):
    result={}
    total=0.0 
    for row in book.itertuples():
        shock=shocks.get(row.leg,0.0)
        leg_pnl=row.signed_qty*row.current_price*shock
        result[row.leg]=leg_pnl
        total += leg_pnl
    result["TOTAL"] = total
    return result


LIMITS={"Gas":2_500_000, "Carbon":2_500_000, "Power":4_000_000, "VaR":300_000,}
def check_limits(book, var_value):
    alerts = []
    for row in book.itertuples():
        exposure = abs(row.signed_qty * row.current_price)
        limit = LIMITS.get(row.leg, float("inf"))
        alerts.append({
            "item": row.leg,
            "exposure": exposure,
            "limit": limit,
            "pct_used": exposure / limit * 100,
            "status": "BREACH" if exposure > limit else "ok",
        })
    alerts.append({
        "item": "Portfolio VaR",
        "exposure": var_value,
        "limit": LIMITS["VaR"],
        "pct_used": var_value / LIMITS["VaR"] * 100,
        "status": "BREACH" if var_value > LIMITS["VaR"] else "ok",})
    return alerts


if __name__ =="__main__":
    history= get_price_history()
    latest={leg: round(history[leg].iloc[-1],2) for leg in history.columns}
    print("\nLatest prices:", latest)
    book = load_positions()
    book=pnl_by_leg(book, latest)


    print("\nP&L attribution by leg:")
    for row in book.itertuples():
        print(f"{row.leg:<8} {row.direction:<6} P&L: {row.pnl:>12,.0f}")
    print(f"{'TOTAL':<8} {'':<6} P&L: {book['pnl'].sum():>12,.0f}")
    print("\nValue at Risk (1-day, 95%):")
    print(f" Historical Var: {historical_var(history, book):>12,.0f}")
    print(f"  Parametric VaR: {parametric_var(history, book):>12,.0f}")
    print("\nStress testing & scenario analysis:") 
    for name, shocks in SCENARIOS.items():
        outcome = stress_test(book, shocks)
        print(f"  {name:<32} P&L: {outcome['TOTAL']:>14,.0f}")
        print("\nPosition-limit checks:")
        var_now = historical_var(history, book)
        for a in check_limits(book, var_now):
            flag = "  *** BREACH ***" if a["status"] == "BREACH" else ""
            print(f"  {a['item']:<14} {a['exposure']:>12,.0f} / {a['limit']:>12,.0f}  ({a['pct_used']:>5.0f}%){flag}")