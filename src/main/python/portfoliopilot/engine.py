# engine.py
import configparser
import os
import csv
import yfinance as yf
import pandas as pd

from portfolio.risk import PortfolioRiskManager
from portfolio.optimizer import PortfolioWeightAllocator
from portfolio.rebalancing import PortfolioRebalanceController
from backtesting.trade_costs import TradeCostCalculator
from backtesting.backtest_engine import HistoricalSimulationEngine
from backtesting.performance_plotter import PortfolioPerformancePlotter

from strategies.momentum import MomentumSignalModule
from strategies.swing import SwingTradingStrategy
from strategies.long_term import LongTermValueStrategy


class ModularPortfolioEngine:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))

        self.risk_manager = PortfolioRiskManager(max_concentration=0.25)
        self.cost_calculator = TradeCostCalculator(platform="DISCOUNT")
        self.rebalance_controller = PortfolioRebalanceController(allowed_drift_threshold=0.05)

        self.momentum_strategy = MomentumSignalModule()
        self.swing_strategy = SwingTradingStrategy()
        self.long_term_strategy = LongTermValueStrategy()
        self.portfolio_optimizer = PortfolioWeightAllocator()
        self.load_configuration()

    def load_configuration(self):
        self.config.read(self.config_path)
        self.country = self.config.get("MARKET_SETTINGS", "market_country", fallback="US").strip().upper()
        self.start_date = self.config.get("BACKTEST_SETTINGS", "start_date", fallback="2024-01-01").strip()
        self.end_date = self.config.get("BACKTEST_SETTINGS", "end_date", fallback="2024-06-30").strip()
        self.initial_budget = self.config.getfloat("MARKET_SETTINGS", "total_budget", fallback=50000.00)
        self.active_analyst_id = self.config.get("MARKET_SETTINGS", "active_analyst",
                                                 fallback="TECHNICAL_ANALYST").strip().upper()
        self.tech_lookback = self.config.getint("ANALYST_LOOKBACK_SETTINGS", "technical_lookback_weeks", fallback=12)

    def broad_market_data_pool(self) -> list:
        if self.country == "IN":
            return [
                "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS", "SBIN.NS", "ITC.NS",
                "HINDUNILVR.NS", "LT.NS",
                "AXISBANK.NS", "WIPRO.NS", "MARUTI.NS", "TITAN.NS", "ULTRACEMCO.NS", "GRASIM.NS", "BAJFINANCE.NS",
                "NESTLEIND.NS", "TECHM.NS",
                "TATASTEEL.NS", "JIOFIN.NS", "SUZLON.NS", "IDEA.NS", "YESBANK.NS"
            ]
        return ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]

    def run_simulation(self):
        self.load_configuration()
        raw_market_pool = self.broad_market_data_pool()

        print(f"📡 Downloading market data metrics for tracking timeline...")
        print(f"🎯 Routing to Target Strategy Module: [{self.active_analyst_id}]")

        # Download with deep calendar padding to protect against lookback starvation traps
        market_data = \
        yf.download(raw_market_pool, start="2023-06-01", end=self.end_date, interval="1d", progress=False)['Close']
        fridays = market_data[market_data.index.dayofweek == 4]

        execution_fridays = fridays[fridays.index >= self.start_date]
        current_cash = self.initial_budget
        holdings_tracker = {}  # Systemic open positions tracker state map

        output_dir = os.path.dirname(self.config_path)
        ledger_file = os.path.join(output_dir, "backtest_ledger.csv")

        with open(ledger_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(
                ["Cycle_Num", "Date", "Ticker", "Asset_Tier", "Quantity", "Price", "Friction_Cost", "Action"])

        for i in range(len(execution_fridays) - 1):
            cycle_start_date = execution_fridays.index[i]
            cycle_end_date = execution_fridays.index[i + 1]
            historical_slice = fridays[fridays.index <= cycle_end_date].tail(self.tech_lookback)

            # --- RECOMMENDATIONS & MONITORING REBALANCING PASS ---
            current_tier_values = {"LARGE_CAP": 0.0, "MID_CAP": 0.0, "RISKY": 0.0}
            total_portfolio_value = current_cash

            for tk, data in list(holdings_tracker.items()):
                current_price = fridays.loc[cycle_end_date, tk]
                if not pd.isna(current_price) and current_price > 0:
                    asset_value = data["shares"] * current_price
                    current_tier_values[data["tier"]] += asset_value
                    total_portfolio_value += asset_value

            target_weights = {"LARGE_CAP": 0.50, "MID_CAP": 0.30, "RISKY": 0.20}
            drift_assessment = self.rebalance_controller.evaluate_allocation_drift(current_tier_values,
                                                                                   total_portfolio_value,
                                                                                   target_weights)

            # Low-Turnover Rebalancing Trigger Strategy
            if drift_assessment.get("rebalance_needed", True) or i % 4 == 0:
                for tk, data in list(holdings_tracker.items()):
                    end_price = fridays.loc[cycle_end_date, tk]
                    if not pd.isna(end_price) and end_price > 0:
                        gross_value = data["shares"] * end_price
                        frictions = self.cost_calculator.calculate_frictions(gross_value)
                        current_cash += (gross_value - frictions)

                        with open(ledger_file, mode='a', newline='') as file:
                            csv.writer(file).writerow(
                                [i + 1, cycle_end_date.date(), tk, data["tier"], data["shares"], end_price,
                                 round(frictions, 2), "SELL"])
                holdings_tracker.clear()

            new_portfolio_selections = []
            total_allocatable_snapshot = current_cash

            for section in self.config.sections():
                if section.endswith("_TIER"):
                    tier_name = section.replace("_TIER", "")
                    weight = self.config.getfloat(section, "weight")
                    max_allowed = self.config.getint(section, "max_tickers")
                    tier_cash_budget = total_allocatable_snapshot * weight

                    strategy_picks = pd.DataFrame()

                    if "TECHNICAL" in self.active_analyst_id or "MOMENTUM" in self.active_analyst_id:
                        strategy_picks = self.momentum_strategy.pick_top_tickers(historical_slice, raw_market_pool,
                                                                                 max_allowed)
                    elif "SWING" in self.active_analyst_id:
                        strategy_picks = self.swing_strategy.generate_reversion_triggers(historical_slice.tail(5),
                                                                                         raw_market_pool).head(
                            max_allowed)
                    elif "LONG" in self.active_analyst_id:
                        strategy_picks = self.long_term_strategy.filter_universe(
                            fridays[fridays.index <= cycle_end_date], raw_market_pool).head(max_allowed)

                    if strategy_picks is None or strategy_picks.empty:
                        continue

                    if 'Return' in strategy_picks.columns:
                        strategy_picks = strategy_picks.rename(columns={'Return': 'Score'})
                    elif 'Score' not in strategy_picks.columns and len(strategy_picks.columns) >= 2:
                        strategy_picks.columns = ['Ticker', 'Score', 'Price']

                    calculated_orders = self.portfolio_optimizer.compute_share_bounds(strategy_picks, tier_cash_budget)

                    for order in calculated_orders:
                        tk = order['Ticker']
                        pr = order['Price']
                        sh = order['Shares']

                        proposed_allocation = sh * pr
                        if not self.risk_manager.inspect_order_safety(proposed_allocation, total_allocatable_snapshot):
                            continue

                        buy_frictions = self.cost_calculator.calculate_frictions(proposed_allocation)
                        if current_cash >= (proposed_allocation + buy_frictions):
                            current_cash -= (proposed_allocation + buy_frictions)

                            holdings_tracker[tk] = {"shares": sh, "tier": tier_name}
                            new_portfolio_selections.append(
                                {'Ticker': tk, 'Tier': tier_name, 'Shares': sh, 'Cost_Basis': pr})

                            with open(ledger_file, mode='a', newline='') as file:
                                csv.writer(file).writerow(
                                    [i + 1, cycle_end_date.date(), tk, tier_name, sh, pr, round(buy_frictions, 2),
                                     "BUY"])

            active_portfolio = pd.DataFrame(new_portfolio_selections)

        # Final Settlement liquidation pass at backtest completion
        final_date = execution_fridays.index[-1]
        for tk, data in list(holdings_tracker.items()):
            end_price = fridays.loc[final_date, tk]
            if not pd.isna(end_price) and end_price > 0:
                gross_value = data["shares"] * end_price
                frictions = self.cost_calculator.calculate_frictions(gross_value)
                current_cash += (gross_value - frictions)
                with open(ledger_file, mode='a', newline='') as file:
                    csv.writer(file).writerow(
                        [999, final_date.date(), tk, data["tier"], data["shares"], end_price, round(frictions, 2),
                         "SELL"])

        print(f"🏁 System simulation loops completed safely.")
        analyzer = HistoricalSimulationEngine(initial_capital=self.initial_budget)
        analyzer.process_ledger_results(ledger_file_path=ledger_file)

        plotter = PortfolioPerformancePlotter(initial_capital=self.initial_budget)
        plotter.generate_equity_chart(ledger_file_path=ledger_file)

        # To this (forces a fresh disk file generation):
        plotter.generate_equity_chart(ledger_file_path=ledger_file, output_image_name="performance_curve_v2.png")