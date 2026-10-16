# backtesting/orchestrator.py
import os
import csv
import sys
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from portfolio.optimizer import PortfolioWeightAllocator
from backtesting.backtest_engine import HistoricalSimulationEngine


class BacktestOrchestrator:
    def __init__(self, settings: dict, strategy_plugin, analyst_plugins: list, friction_engine, risk_engine):
        self.settings = settings
        self.strategy = strategy_plugin
        self.analyst_plugins = analyst_plugins
        self.friction_engine = friction_engine
        self.risk_manager = risk_engine
        self.portfolio_optimizer = PortfolioWeightAllocator()

    def execute_simulation_timeline(self, raw_market_pool: list, preloaded_data: pd.DataFrame,
                                    ledger_file_path: str) -> dict:
        if preloaded_data.empty:
            print("   ⚠️ Preloaded data matrix is unpopulated.")
            return {}

        valid_pool_tickers = [t for t in raw_market_pool if t in preloaded_data.columns]
        if not valid_pool_tickers:
            print("   ⚠️ No matching universe assets found in download blocks.")
            return {}

        execution_timeline = preloaded_data[preloaded_data.index >= self.settings["start_date"]]
        if len(execution_timeline) < 2:
            print(f"   ⚠️ Timeline contains insufficient tracking slots ({len(execution_timeline)}). Skipping.")
            return {}

        initial_budget = self.settings["initial_budget"]
        current_cash = initial_budget
        holdings_tracker, total_taxes = {}, 0.0
        peak_valuation = initial_budget

        total_days_count = len(execution_timeline) - 1

        for i in range(total_days_count):
            cycle_date = execution_timeline.index[i + 1]

            if i % int(self.settings["rebalance_days"]) == 0 and holdings_tracker:
                for tk, data in list(holdings_tracker.items()):
                    if tk not in preloaded_data.columns: continue
                    pr_raw = float(preloaded_data.loc[cycle_date, tk])
                    if pd.isna(pr_raw) or pr_raw <= 0: continue

                    fx = 1.0
                    if not tk.endswith(".NS") and "USDINR=X" in preloaded_data.columns:
                        fx = float(preloaded_data.loc[cycle_date, "USDINR=X"])

                    if pd.isna(fx) or fx <= 0: fx = 1.0
                    pr_base = pr_raw * fx
                    val_base = data["shares"] * pr_base

                    friction = self.friction_engine.calculate_trade_leakage(tk, val_base, "SELL")
                    tax = self.friction_engine.calculate_capital_gains_tax(data["buy_date"], cycle_date,
                                                                           data["buy_price_base"], pr_base,
                                                                           data["shares"])

                    total_taxes += tax
                    current_cash += (val_base - friction - tax)
                    with open(ledger_file_path, mode='a', newline='') as f:
                        csv.writer(f).writerow(
                            [f"{self.settings['experiment_label']}_{i + 1}", cycle_date.date(), tk, "LARGE_CAP",
                             data["shares"], pr_raw, friction, "SELL"])
                holdings_tracker.clear()

            # FIXED: Corrected 'daily_prices' reference targets to point cleanly to 'preloaded_data'
            current_portfolio_value = 0.0
            for tk, data in holdings_tracker.items():
                if tk in preloaded_data.columns:
                    current_portfolio_value += data["shares"] * float(preloaded_data.loc[cycle_date, tk])

            total_valuation = current_cash + current_portfolio_value
            if total_valuation > peak_valuation:
                peak_valuation = total_valuation

            current_drawdown = (total_valuation - peak_valuation) / peak_valuation if peak_valuation > 0 else 0.0
            risk_scaling_factor = self.risk_manager.adjust_risk_profile(current_drawdown)

            if current_cash <= 100.0 or risk_scaling_factor <= 0:
                continue

            total_allocatable = current_cash * risk_scaling_factor * 0.95
            historical_slice = preloaded_data[valid_pool_tickers][preloaded_data.index <= cycle_date].tail(
                self.settings["tech_lookback"])

            raw_strategy_picks = self.strategy.generate_signals(historical_slice, valid_pool_tickers,
                                                                len(valid_pool_tickers))
            if raw_strategy_picks.empty: continue

            fused_rankings = []
            for _, pick in raw_strategy_picks.iterrows():
                tk = pick['Ticker']
                base_score, pr = abs(float(pick['Score'])), float(pick['Price'])
                if pd.isna(pr) or pr <= 0: continue

                fused_multiplier = 1.0
                for plugin in self.analyst_plugins:
                    fused_multiplier *= plugin.calculate_factor_multiplier(tk, historical_slice)

                fused_score = base_score * fused_multiplier
                if fused_score > 0:
                    fused_rankings.append({'Ticker': tk, 'Score': fused_score, 'Price': pr})

            fused_df = pd.DataFrame(fused_rankings)
            if fused_df.empty: continue

            fused_df = fused_df.sort_values(by="Score", ascending=False).head(int(self.settings["max_tickers"]))
            calculated_orders = self.portfolio_optimizer.compute_share_bounds(fused_df, total_allocatable)

            for order in calculated_orders:
                tk, pr_raw, sh = order['Ticker'], order['Price'], order['Shares']
                fx = 1.0
                if not tk.endswith(".NS") and "USDINR=X" in preloaded_data.columns:
                    fx = float(preloaded_data.loc[cycle_date, "USDINR=X"])

                if pd.isna(fx) or fx <= 0: fx = 1.0
                pr_base = pr_raw * fx
                alloc_base = sh * pr_base
                buy_friction = self.friction_engine.calculate_trade_leakage(tk, alloc_base, "BUY")
                total_cost = alloc_base + buy_friction

                if current_cash >= total_cost and tk not in holdings_tracker:
                    current_cash -= total_cost
                    holdings_tracker[tk] = {"shares": sh, "buy_date": cycle_date, "buy_price_base": pr_base}
                    with open(ledger_file_path, mode='a', newline='') as f:
                        csv.writer(f).writerow(
                            [f"{self.settings['experiment_label']}_{i + 1}", cycle_date.date(), tk, "LARGE_CAP", sh,
                             pr_raw, buy_friction, "BUY"])

        # FIXED: Corrected 'daily_prices' references to 'preloaded_data' in the final liquidation loop
        if holdings_tracker:
            final_date = execution_timeline.index[-1]
            for tk, data in list(holdings_tracker.items()):
                if tk in preloaded_data.columns:
                    pr_raw = float(preloaded_data.loc[final_date, tk])
                    if pd.isna(pr_raw) or pr_raw <= 0: continue
                    fx = 1.0
                    if not tk.endswith(".NS") and "USDINR=X" in preloaded_data.columns:
                        fx = float(preloaded_data.loc[final_date, "USDINR=X"])
                    if pd.isna(fx) or fx <= 0: fx = 1.0
                    current_cash += (data["shares"] * (pr_raw * fx) - 20.0)
                    with open(ledger_file_path, mode='a', newline='') as f:
                        csv.writer(f).writerow(
                            [999, final_date.date(), tk, "LARGE_CAP", data["shares"], pr_raw, 20.0, "SELL"])

        metrics = HistoricalSimulationEngine(self.settings["initial_budget"]).process_ledger_results(
            ledger_file_path=ledger_file_path)
        if metrics:
            metrics["Total Taxes Paid (INR)"] = round(total_taxes, 2)
            return metrics
        return {}
