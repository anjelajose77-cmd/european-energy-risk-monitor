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
print(f" Paramtric Var: {parametric_var(history, book):>12,.0f}")