# backtesting/backtest_engine.py
import os
import pandas as pd
import numpy as np


class HistoricalSimulationEngine:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital

    def process_ledger_results(self, ledger_file_path: str) -> dict:
        if not os.path.exists(ledger_file_path):
            print(f"❌ Error: Ledger file not found at {ledger_file_path}")
            return {}

        df = pd.read_csv(ledger_file_path)
        if df.empty:
            print("⚠️ Warning: Ledger file is completely empty.")
            return {}

        # FIXED: Enforced a clean dynamic column name normalization routine
        df.columns = [col.strip() for col in df.columns]

        # Guardrail check against missing columns to prevent hard KeyError drops
        if 'Date' not in df.columns or 'Action' not in df.columns:
            print("⚠️ Warning: Ledger matrix columns are unaligned.")
            return {}

        unique_dates = sorted(df['Date'].unique())
        current_cash = self.initial_capital
        holdings = {}
        equity_curve = []
        dates = []

        for date in unique_dates:
            day_actions = df[df['Date'] == date]

            sells = day_actions[day_actions['Action'] == 'SELL']
            for _, row in sells.iterrows():
                tk = row['Ticker']
                qty = int(row['Quantity'])
                price = float(row['Price'])
                friction = float(row['Friction_Cost'])

                current_cash += (qty * price - friction)
                if tk in holdings:
                    holdings[tk] = max(0, holdings[tk] - qty)
                    if holdings[tk] == 0:
                        del holdings[tk]

            buys = day_actions[day_actions['Action'] == 'BUY']
            for _, row in buys.iterrows():
                tk = row['Ticker']
                qty = int(row['Quantity'])
                price = float(row['Price'])
                friction = float(row['Friction_Cost'])

                current_cash -= (qty * price + friction)
                holdings[tk] = holdings.get(tk, 0) + qty

            portfolio_value = 0.0
            for open_ticker, open_shares in holdings.items():
                ticker_transactions = day_actions[day_actions['Ticker'] == open_ticker]
                if not ticker_transactions.empty:
                    current_price = float(ticker_transactions.iloc[-1]['Price'])
                else:
                    fallback_rows = df[(df['Ticker'] == open_ticker) & (df['Date'] <= date)]
                    current_price = float(fallback_rows.iloc[-1]['Price']) if not fallback_rows.empty else 0.0

                portfolio_value += (open_shares * current_price)

            total_equity = current_cash + portfolio_value
            if not day_actions.empty and int(
                    day_actions.iloc[-1]['Cycle_Num'].split('_')[-1] if isinstance(day_actions.iloc[-1]['Cycle_Num'],
                                                                                   str) else day_actions.iloc[-1][
                        'Cycle_Num']) != 999:
                equity_curve.append(total_equity)
                dates.append(pd.to_datetime(date))

        if not equity_curve:
            return {
                "Initial Capital": self.initial_capital,
                "Final Valuation": self.initial_capital,
                "Net Return (%)": 0.0,
                "Total Friction Fees Paid": 0.0,
                "Annualized Volatility (%)": 0.0,
                "Sharpe Ratio": 0.0,
                "Max Drawdown (%)": 0.0
            }

        equity_series = pd.Series(equity_curve, index=dates)
        returns_series = equity_series.pct_change().dropna()

        final_value = equity_series.iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital
        total_frictions_paid = df['Friction_Cost'].sum()

        ann_factor = 52
        std_dev = returns_series.std()
        annualized_volatility = std_dev * np.sqrt(ann_factor) if std_dev > 0 else 0.0
        mean_return = returns_series.mean()
        sharpe_ratio = (mean_return / (std_dev + 1e-9)) * np.sqrt(ann_factor) if std_dev > 0 else 0.0

        rolling_max = equity_series.cummax()
        drawdowns = (equity_series - rolling_max) / rolling_max
        max_drawdown = drawdowns.min() if not drawdowns.empty else 0.0

        performance_report = {
            "Initial Capital": round(self.initial_capital, 2),
            "Final Valuation": round(final_value, 2),
            "Net Return (%)": round(total_return * 100, 2),
            "Total Friction Fees Paid": round(total_frictions_paid, 2),
            "Annualized Volatility (%)": round(annualized_volatility * 100, 2),
            "Sharpe Ratio": round(sharpe_ratio, 2),
            "Max Drawdown (%)": round(max_drawdown * 100, 2)
        }

        self.display_report_card(performance_report)
        return performance_report

    def display_report_card(self, metrics: dict):
        print("\n==================================================================")
        print("    📊  PORTFOLIO PILOT BACKTEST PERFORMANCE REPORT CARD  📊")
        print("==================================================================")
        for key, value in metrics.items():
            if "%)" in key:
                print(f" 📈 {key:<30} : {value}%")
            elif "Ratio" in key:
                print(f" 🎯 {key:<30} : {value}")
            else:
                print(f" 💵 {key:<30} : {value:,.2f}" if isinstance(value, (int, float)) and (
                            "Capital" in key or "Valuation" in key) else f" 💵 {key:<30} : {value}")
        print("==================================================================\n")
