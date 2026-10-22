# backtesting/orchestrator.py - PART 1
import os
import csv
import sys
import pandas as pd
import numpy as np

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

    def _extract_scalar(self, value) -> float:
        if isinstance(value, (pd.Series, pd.DataFrame, np.ndarray)):
            if value.size == 0: return 0.0
            val = value.values.flatten()[-1]
            return float(val) if not pd.isna(val) else 0.0
        return float(value) if (value is not None and not pd.isna(value)) else 0.0

    def execute_simulation_timeline(self, raw_market_pool: list, preloaded_data: pd.DataFrame,
                                    ledger_file_path: str) -> dict:
        if preloaded_data.empty: return {}

        preloaded_data = preloaded_data.copy()
        preloaded_data.columns = [col.strip().upper() for col in preloaded_data.columns]

        valid_pool_tickers = [str(t).strip().upper() for t in raw_market_pool if
                              str(t).strip().upper() in preloaded_data.columns]
        if not valid_pool_tickers: return {}

        execution_timeline = preloaded_data[preloaded_data.index >= self.settings["start_date"]]
        if len(execution_timeline) < 2: return {}

        initial_budget = float(self.settings["initial_budget"])
        current_cash = initial_budget
        holdings_tracker, total_taxes = {}, 0.0
        peak_valuation = initial_budget

        strategy_name = str(self.settings.get("s_name", "MOMENTUM")).upper()
        analyst_run_id = str(self.settings.get("a_name", "DEFAULT_ANALYST"))
        print(
            f"   ⚡ Launching Point-in-Time Multiplicative Engine for Strategy: [{strategy_name}] | Analyst: [{analyst_run_id}]...")

        total_days_count = len(execution_timeline) - 1

        for i in range(total_days_count):
            cycle_date = execution_timeline.index[i + 1]
            liquidated_today = set()

            # 1. SCAN FOR STOP-LOSS VIOLATIONS (SAFE ISOLATED PASS)
            if holdings_tracker:
                violated_tickers = []
                for tk, data in holdings_tracker.items():
                    if tk not in preloaded_data.columns: continue
                    pr_raw = self._extract_scalar(preloaded_data.loc[cycle_date, tk])
                    if pr_raw <= 0: continue

                    if "peak_price" not in data or data["peak_price"] <= 0:
                        data["peak_price"] = data["buy_price_base"]

                    fx = 1.0
                    if not tk.endswith(".NS") and "USDINR=X" in preloaded_data.columns:
                        fx = self._extract_scalar(preloaded_data.loc[cycle_date, "USDINR=X"])
                    if fx <= 0 or pd.isna(fx): fx = 1.0

                    pr_base = pr_raw * fx
                    if pr_base > data["peak_price"]:
                        data["peak_price"] = pr_base

                    # FIXED: Explicit lookup checks experiment label and universe variables cleanly
                    if strategy_name == "SWING":
                        is_mid_cap = "MID_CAP" in str(self.settings.get("u_name", "")).upper() or "MID_CAP" in str(
                            self.settings.get("experiment_label", "")).upper()
                        stop_loss_pct = 0.03 if is_mid_cap else 0.05
                    else:
                        stop_loss_pct = 0.15

                    drawdown_from_peak = (pr_base - data["peak_price"]) / data["peak_price"]

                    if drawdown_from_peak <= -stop_loss_pct:
                        violated_tickers.append((tk, pr_raw, pr_base))

                for tk, pr_raw, pr_base in violated_tickers:
                    data = holdings_tracker[tk]
                    val_base = data["shares"] * pr_base
                    friction = self.friction_engine.calculate_trade_leakage(tk, val_base, "SELL")
                    tax = self.friction_engine.calculate_capital_gains_tax(
                        data["buy_date"], cycle_date, data["buy_price_base"], pr_base, data["shares"]
                    )

                    total_taxes += tax
                    current_cash += (val_base - friction - tax)
                    liquidated_today.add(tk)
                    del holdings_tracker[tk]

                    with open(ledger_file_path, mode='a', newline='') as f:
                        csv.writer(f).writerow([
                            f"{self.settings['experiment_label']}_{i + 1}_STOP",
                            cycle_date.date(), tk, self.settings["u_name"],
                            data["shares"], pr_raw, friction, "SELL"
                        ])

            # 2. STANDARD STRATEGY REBALANCE SCHEDULE ROUTER
            is_rebalance_cycle = False
            if strategy_name == "SWING":
                if i % int(self.settings["rebalance_days"]) == 0:
                    is_rebalance_cycle = True
            elif strategy_name == "MOMENTUM":
                if i % int(self.settings["rebalance_days"]) == 0:
                    is_rebalance_cycle = True
            elif strategy_name in ["LONG_TERM", "OPTIONS"]:
                is_rebalance_cycle = False

            if is_rebalance_cycle and holdings_tracker:
                for tk, data in list(holdings_tracker.items()):
                    if tk not in preloaded_data.columns: continue
                    pr_raw = self._extract_scalar(preloaded_data.loc[cycle_date, tk])
                    if pr_raw <= 0: continue

                    fx = 1.0
                    if not tk.endswith(".NS") and "USDINR=X" in preloaded_data.columns:
                        fx = self._extract_scalar(preloaded_data.loc[cycle_date, "USDINR=X"])
                    if fx <= 0 or pd.isna(fx): fx = 1.0

                    pr_base = pr_raw * fx
                    val_base = data["shares"] * pr_base

                    friction = self.friction_engine.calculate_trade_leakage(tk, val_base, "SELL")
                    tax = self.friction_engine.calculate_capital_gains_tax(
                        data["buy_date"], cycle_date, data["buy_price_base"], pr_base, data["shares"]
                    )

                    total_taxes += tax
                    current_cash += (val_base - friction - tax)
                    liquidated_today.add(tk)

                    with open(ledger_file_path, mode='a', newline='') as f:
                        csv.writer(f).writerow([
                            f"{self.settings['experiment_label']}_{i + 1}",
                            cycle_date.date(), tk, self.settings["u_name"],
                            data["shares"], pr_raw, friction, "SELL"
                        ])
                holdings_tracker.clear()
# backtesting/orchestrator.py - PART 2
            # 3. DAILY VALUE RECONSTRUCTION & METRIC EVALUATION
            current_portfolio_value = 0.0
            for tk, data in holdings_tracker.items():
                if tk in preloaded_data.columns:
                    pr_tk = self._extract_scalar(preloaded_data.loc[cycle_date, tk])
                    current_portfolio_value += data["shares"] * pr_tk

            total_valuation = current_cash + current_portfolio_value
            if total_valuation > peak_valuation: peak_valuation = total_valuation

            current_drawdown = (total_valuation - peak_valuation) / peak_valuation if peak_valuation > 0 else 0.0
            risk_scaling_factor = self.risk_manager.adjust_risk_profile(current_drawdown)

            if current_cash <= 100.0 or risk_scaling_factor <= 0: continue

            # STRATEGY SIGNAL EXECUTION INTERCEPT
            if strategy_name == "SWING" and i % int(self.settings["rebalance_days"]) != 0: continue
            if strategy_name == "MOMENTUM" and i % int(self.settings["rebalance_days"]) != 0: continue
            if strategy_name in ["LONG_TERM", "OPTIONS"] and len(holdings_tracker) >= int(self.settings.get("max_tickers", 8)): continue

            total_allocatable = current_cash * risk_scaling_factor * float(self.settings["tier_weight"]) * 0.95
            historical_slice = preloaded_data[valid_pool_tickers][preloaded_data.index <= cycle_date].tail(int(self.settings["tech_lookback"]))

            if strategy_name == "OPTIONS":
                index_ma = historical_slice["^BSESN"].tail(5).mean() if "^BSESN" in historical_slice.columns else 1.0
                current_index = historical_slice["^BSESN"].iloc[-1] if "^BSESN" in historical_slice.columns else 1.0
                if current_index < index_ma:
                    current_cash += current_cash * (0.07 / 252)
                    continue

            max_allowed_assets = int(self.settings.get("max_tickers", 8))

            orchestrator_multipliers = {}
            for tk_check in valid_pool_tickers:
                fused_m = 1.0
                for plugin in self.analyst_plugins:
                    try:
                        if hasattr(plugin, 'calculate_factor_multiplier'):
                            fused_m *= float(plugin.calculate_factor_multiplier(tk_check, historical_slice, cycle_date))
                    except Exception:
                        fused_m *= 1.0
                orchestrator_multipliers[tk_check] = fused_m

            if hasattr(self.strategy, 'set_active_multipliers'):
                self.strategy.set_active_multipliers(orchestrator_multipliers)

            raw_strategy_picks = self.strategy.generate_signals(historical_slice, valid_pool_tickers, len(valid_pool_tickers))
            if raw_strategy_picks.empty: continue

            fused_rankings = []
            for _, pick in raw_strategy_picks.iterrows():
                tk = str(pick['Ticker']).strip().upper()
                pr = self._extract_scalar(pick['Price'])

                if pr <= 0 or tk in holdings_tracker or tk in liquidated_today: continue

                base_score = self._extract_scalar(pick['Score'])
                fused_multiplier = orchestrator_multipliers.get(tk, 1.0)

                fused_score = float(base_score) * float(fused_multiplier) * 100.0
                uniqueness_salt = (sum(ord(c) for c in tk) % 1000) * 0.00001
                fused_score += uniqueness_salt

                fused_rankings.append({'Ticker': tk, 'Score': fused_score, 'Price': pr})

            fused_df = pd.DataFrame(fused_rankings)
            if fused_df.empty: continue

            space_left = max_allowed_assets - len(holdings_tracker)
            if space_left <= 0: continue

            fused_df = fused_df.sort_values(by="Score", ascending=False).head(space_left)
            calculated_orders = self.portfolio_optimizer.compute_share_bounds(fused_df, total_allocatable)

            for order in calculated_orders:
                tk, pr_raw, sh = order['Ticker'], order['Price'], order['Shares']
                fx = 1.0
                if not tk.endswith(".NS") and "USDINR=X" in preloaded_data.columns:
                    fx = self._extract_scalar(preloaded_data.loc[cycle_date, "USDINR=X"])
                if fx <= 0 or pd.isna(fx): fx = 1.0

                pr_base = pr_raw * fx
                alloc_base = sh * pr_base
                buy_friction = self.friction_engine.calculate_trade_leakage(tk, alloc_base, "BUY")
                total_cost = alloc_base + buy_friction

                if current_cash >= total_cost and tk not in holdings_tracker:
                    current_cash -= total_cost
                    holdings_tracker[tk] = {"shares": sh, "buy_date": cycle_date, "buy_price_base": pr_base}
                    with open(ledger_file_path, mode='a', newline='') as f:
                        csv.writer(f).writerow([
                            f"{self.settings['experiment_label']}_{i + 1}",
                            cycle_date.date(), tk, self.settings["u_name"],
                            sh, pr_raw, buy_friction, "BUY"
                        ])

        # 4. FINAL CLOSURE PASS
        if holdings_tracker:
            final_date = execution_timeline.index[-1]
            for tk, data in list(holdings_tracker.items()):
                if tk in preloaded_data.columns:
                    pr_raw = self._extract_scalar(preloaded_data.loc[final_date, tk])
                    if pr_raw <= 0: continue
                    fx = 1.0
                    if not tk.endswith(".NS") and "USDINR=X" in preloaded_data.columns:
                        fx = self._extract_scalar(preloaded_data.loc[final_date, "USDINR=X"])
                    if fx <= 0 or pd.isna(fx): fx = 1.0
                    current_cash += (data["shares"] * (pr_raw * fx) - 20.0)
                    with open(ledger_file_path, mode='a', newline='') as f:
                        csv.writer(f).writerow([
                            999, final_date.date(), tk, self.settings["u_name"],
                            data["shares"], pr_raw, 20.0, "SELL"
                        ])

        metrics = HistoricalSimulationEngine(self.settings["initial_budget"]).process_ledger_results(ledger_file_path=ledger_file_path)
        if metrics:
            metrics["Total Taxes Paid (INR)"] = round(total_taxes, 2)
            return metrics
        return {}
