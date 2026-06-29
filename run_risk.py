import os
from datetime import date
from risk_data import get_price_history
from risk_engine import (load_positions,pnl_by_leg,historical_var, parametric_var,SCENARIOS, stress_test,check_limits,)
from excel_report import build_report

def main():
    print("=" * 55)
    print("  EUROPEAN CROSS-COMMODITY RISK MONITOR")
    print(f"  {date.today():%d %B %Y}")
    print("=" * 55)

    history = get_price_history()
    latest = {leg: round(history[leg].iloc[-1], 2) for leg in history.columns}
    book = load_positions()
    book = pnl_by_leg(book, latest)
    total_pnl = book["pnl"].sum()

    var_hist = historical_var(history, book)
    var_param = parametric_var(history, book)
    scenarios = {name: stress_test(book, shocks)["TOTAL"]
                 for name, shocks in SCENARIOS.items()}
    limits = check_limits(book, var_hist)
    os.makedirs("output", exist_ok=True)
    out_path = f"output/risk_report_{date.today():%Y%m%d}.xlsx"
    build_report(latest, book, total_pnl, var_hist, var_param,
                 scenarios, limits, out_path)
    breaches = sum(1 for a in limits if a["status"] == "BREACH")
    print(f"  Total P&L:        {total_pnl:>14,.0f}")
    print(f"  VaR (historical): {var_hist:>14,.0f}")
    print(f"  Limit breaches:   {breaches:>14}")
    print("=" * 55)
    print(f"  Excel report saved: {out_path}")
    print("=" * 55)

if __name__ == "__main__":
    main()