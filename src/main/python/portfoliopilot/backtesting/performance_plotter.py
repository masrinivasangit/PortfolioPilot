# backtesting/performance_plotter.py
import os
import pandas as pd
import matplotlib.pyplot as plt


class PortfolioPerformancePlotter:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital

    def generate_equity_chart(self, ledger_file_path: str, output_image_name: str = "performance_curve_v2.png"):
        """
        Chronologically calculates cash and open asset values across every date
        step to plot an accurate, continuous portfolio equity curve.
        """
        if not os.path.exists(ledger_file_path):
            print(f"⚠️ Performance Plotter skipped: Ledger file missing at {ledger_file_path}")
            return

        df = pd.read_csv(ledger_file_path)
        if df.empty:
            print("⚠️ Performance Plotter skipped: Ledger file contains no data rows.")
            return

        unique_dates = sorted(df['Date'].unique())
        current_cash = self.initial_capital

        # Dynamic share map tracker to remember open positions across weeks
        open_shares = {}  # Schema: {ticker: shares_count}
        equity_values = []
        dates = []

        for date in unique_dates:
            day_actions = df[df['Date'] == date]

            # 1. Process liquidations first to settle cash balance metrics
            sells = day_actions[day_actions['Action'] == 'SELL']
            for _, row in sells.iterrows():
                tk = row['Ticker']
                qty = int(row['Quantity'])
                price = float(row['Price'])
                friction = float(row['Friction_Cost'])

                current_cash += (qty * price - friction)
                if tk in open_shares:
                    open_shares[tk] = max(0, open_shares[tk] - qty)
                    if open_shares[tk] == 0:
                        del open_shares[tk]

            # 2. Process entry purchases
            buys = day_actions[day_actions['Action'] == 'BUY']
            for _, row in buys.iterrows():
                tk = row['Ticker']
                qty = int(row['Quantity'])
                price = float(row['Price'])
                friction = float(row['Friction_Cost'])

                current_cash -= (qty * price + friction)
                open_shares[tk] = open_shares.get(tk, 0) + qty

            # 3. Value ALL open assets using their current market closing price
            portfolio_value = 0.0
            for open_ticker, count in open_shares.items():
                ticker_actions = day_actions[day_actions['Ticker'] == open_ticker]
                if not ticker_actions.empty:
                    # Use today's transaction price if it traded today
                    current_price = float(ticker_actions.iloc[-1]['Price'])
                else:
                    # Otherwise, pull its last known price from historical ledger rows
                    current_price = float(df[(df['Ticker'] == open_ticker) & (df['Date'] <= date)].iloc[-1]['Price'])

                portfolio_value += (count * current_price)

            # True Equity calculation step
            total_equity = current_cash + portfolio_value

            # Skip the final settlement noise row (Cycle 999) to keep the chart clean
            if int(day_actions.iloc[-1]['Cycle_Num']) != 999:
                equity_values.append(total_equity)
                dates.append(pd.to_datetime(date))

        # Render the structural timeline visualization curve
        plt.figure(figsize=(10, 5))
        plt.plot(dates, equity_values, label="Portfolio Equity Curve", color="#1f77b4", linewidth=2.5)
        plt.axhline(y=self.initial_capital, color="red", linestyle="--", alpha=0.6, label="Initial Capital")

        plt.title("PortfolioPilot Strategic Equity Simulation Curve", fontsize=12, fontweight='bold', pad=15)
        plt.xlabel("Timeline Horizons", fontsize=10)
        plt.ylabel("Account Valuation (INR)", fontsize=10)
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.legend(loc="upper left")
        plt.tight_layout()

        output_path = os.path.join(os.path.dirname(ledger_file_path), output_image_name)
        plt.savefig(output_path, dpi=300)
        plt.close()
        print(f"📊 Corrected Chart generated successfully! Saved at: {output_path}")
