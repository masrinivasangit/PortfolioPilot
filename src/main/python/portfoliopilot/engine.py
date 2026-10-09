# engine.py
import configparser
import os
import csv
import yfinance as yf
import pandas as pd
from datetime import datetime

from signals import MomentumSignalModule


class ModularPortfolioEngine:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.picker_tool = MomentumSignalModule()
        self.load_configuration()

    def load_configuration(self):
        self.config.read(self.config_path)
        self.country = self.config.get("MARKET_SETTINGS", "market_country", fallback="US").upper()
        self.start_date = self.config.get("BACKTEST_SETTINGS", "start_date", fallback="2024-01-01")
        self.end_date = self.config.get("BACKTEST_SETTINGS", "end_date", fallback="2024-06-30")
        self.initial_budget = self.config.getfloat("MARKET_SETTINGS", "total_budget", fallback=50000.00)

    def extract_custom_pools(self) -> dict:
        """Dynamically loops through ALL sections ending with _TIER from the text config."""
        universes = {}
        for section in self.config.sections():
            if section.endswith("_TIER"):
                tier_name = section.replace("_TIER", "")
                weight = self.config.getfloat(section, "weight")
                max_tickers = self.config.getint(section, "max_tickers")

                # Check if it points to an index sweep or a custom list string
                if self.config.get(section, "source_index", fallback="") == "LARGE_INDEX":
                    if self.country == "IN":
                        # Scrape live Nifty 50 tokens from Wikipedia
                        try:
                            payload = pd.read_html('https://wikipedia.org')
                            pool = (payload[1]['Symbol'] + ".NS").tolist()
                        except Exception:
                            # Robust fallback seed pool if online scraping hits timeout limits
                            pool = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS",
                                    "SBIN.NS"]
                    else:
                        try:
                            payload = pd.read_html('https://wikipedia.org')
                            pool = payload[0]['Symbol'].str.replace('.', '-', regex=False).tolist()
                        except Exception:
                            pool = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]
                else:
                    # Natively parse comma-separated custom lists for MID, SMALL, or RISKY tiers
                    raw_pool = self.config.get(section, f"custom_pool_{self.country}", fallback="")
                    pool = [t.strip() for t in raw_pool.split(",") if t.strip()]

                universes[tier_name] = {"weight": weight, "max_tickers": max_tickers, "pool": pool}
        return universes

    def run_simulation(self):
        self.load_configuration()
        universes = self.extract_custom_pools()

        # Flatten all custom pools into a single unique array to request batch data
        all_tickers = []
        for tier, settings in universes.items():
            all_tickers.extend(settings["pool"])
        all_tickers = list(set(all_tickers))

        print(f"📡 Downloading market data stream for {len(all_tickers)} unique tickers...")
        market_data = yf.download(all_tickers, start=self.start_date, end=self.end_date, interval="1d", progress=False)[
            'Close']
        fridays = market_data[market_data.index.dayofweek == 4]

        current_cash = self.initial_budget
        active_portfolio = pd.DataFrame(columns=['Ticker', 'Tier', 'Shares', 'Cost_Basis'])

        output_dir = os.path.dirname(self.config_path)
        ledger_file = os.path.join(output_dir, "backtest_ledger.csv")

        with open(ledger_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Cycle_Num", "Date", "Ticker", "Asset_Tier", "Quantity", "Price", "Action"])

        # Run through history step-by-step
        for i in range(len(fridays) - 1):
            cycle_start_date = fridays.index[i]
            cycle_end_date = fridays.index[i + 1]

            # 1. Sell existing holdings to collect liquid cash resources
            if not active_portfolio.empty:
                for _, row in active_portfolio.iterrows():
                    end_price = fridays.loc[cycle_end_date, row['Ticker']]
                    if not pd.isna(end_price) and end_price > 0:
                        current_cash += row['Shares'] * end_price
                        with open(ledger_file, mode='a', newline='') as file:
                            csv.writer(file).writerow(
                                [i + 1, cycle_end_date.date(), row['Ticker'], row['Tier'], row['Shares'], end_price,
                                 "SELL"])
            active_portfolio = pd.DataFrame(columns=['Ticker', 'Tier', 'Shares', 'Cost_Basis'])

            # 2. Re-allocate cash assets dynamically across ALL active configured tiers
            weekly_historical_block = fridays.loc[[cycle_start_date, cycle_end_date]]
            new_portfolio_selections = []

            for tier_name, settings in universes.items():
                tier_cash_budget = current_cash * settings["weight"]

                # Call selection plugin tool logic
                top_picks = self.picker_tool.pick_top_tickers(
                    historical_close_data=weekly_historical_block,
                    pool_tickers=settings["pool"],
                    max_allowed=settings["max_tickers"]
                )

                if top_picks.empty:
                    continue

                cash_per_stock = tier_cash_budget / len(top_picks)
                for _, pick in top_picks.iterrows():
                    tk = pick['Ticker']
                    pr = pick['Price']
                    sh = int(cash_per_stock // pr)

                    if sh > 0:
                        current_cash -= (sh * pr)
                        new_portfolio_selections.append(
                            {'Ticker': tk, 'Tier': tier_name, 'Shares': sh, 'Cost_Basis': pr})
                        with open(ledger_file, mode='a', newline='') as file:
                            csv.writer(file).writerow([i + 1, cycle_end_date.date(), tk, tier_name, sh, pr, "BUY"])

            active_portfolio = pd.DataFrame(new_portfolio_selections)

        print(f"🏁 System cycle finished using Sub-Tool: [{self.picker_tool.strategy_name}]")
