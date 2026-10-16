# main.py
import configparser
import os
import csv
import sys
import datetime
import yfinance as yf
import pandas as pd

current_pkg_dir = os.path.dirname(os.path.abspath(__file__))
if current_pkg_dir not in sys.path:
    sys.path.insert(0, current_pkg_dir)

from data.market_data import DataStreamProvider
from strategies.momentum import MomentumSignalModule
from strategies.swing import SwingTradingStrategy
from strategies.long_term import LongTermValueStrategy
from strategies.options import DerivativesOptionsStrategy

from analysis.technical_analyst import TechnicalAnalystAgent
from analysis.fundamental_analyst import FundamentalAnalystAgent
from analysis.news_analyst import NewsAnalystAgent
from analysis.macro_analyst import MacroAnalystAgent
from monitoring.strategy_analyst import SelfAnalysisDecisionEngine
from calculations import QuantitativeMathEngine


class QuantitativeDiscoveryEngine:
    def __init__(self):
        self.config_path = os.path.join(current_pkg_dir, "config.properties")
        self.summary_matrix_path = os.path.join(current_pkg_dir, "optimal_strategy_matrix.csv")
        self.reports_dir = os.path.join(current_pkg_dir, "reports")
        self.config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))

    def execute_grid_search(self):
        print("omsivayanama")
        print("==================================================================")
        print(" ✈️  LAUNCHING FULL-SPECTRUM UNIVERSAL STRATEGY MATRIX ENGINE  ✈️ ")
        print("==================================================================")

        self.config.read(self.config_path)
        market_zone = self.config.get("MARKET_SETTINGS", "market_country", fallback="IN").strip().upper()
        start_date = self.config.get("BACKTEST_SETTINGS", "start_date", fallback="2026-01-01").strip()
        end_date = self.config.get("BACKTEST_SETTINGS", "end_date", fallback="2026-03-31").strip()
        initial_budget = self.config.getfloat("MARKET_SETTINGS", "total_budget", fallback=100000.00)

        api_token = self.config.get("MARKET_SETTINGS", "ai_credential_token", fallback="").strip()
        openai_token = self.config.get("MARKET_SETTINGS", "openai_credential_token", fallback="").strip()

        tech_lookback = self.config.getint("ANALYST_LOOKBACK_SETTINGS", "technical_lookback_weeks", fallback=12)
        macro_lookback = self.config.getint("ANALYST_LOOKBACK_SETTINGS", "macro_lookback_months", fallback=24)
        rebalance_interval_days = self.config.getint("SCHEDULE_SETTINGS", "rebalance_days", fallback=1)

        strategies_pool = {
            "MOMENTUM": MomentumSignalModule(),
            "SWING": SwingTradingStrategy(),
            "LONG_TERM": LongTermValueStrategy(),
            "OPTIONS": DerivativesOptionsStrategy()
        }

        print(f"📡 Downloading live component registries for master screening blocks...")
        full_nifty_registry = DataStreamProvider.scrape_live_index_universe("IN")

        fallback_midcaps = ["TATAELXSI.NS", "KPITTECH.NS", "POLYCAB.NS", "DIXON.NS", "COFORGE.NS", "MAXHEALTH.NS",
                            "PERSISTENT.NS", "CONCOR.NS", "VOLTAS.NS", "CUMMINSIND.NS"]
        fallback_nifty_index = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"]

        universes_pool = {
            "LARGECAP": full_nifty_registry[:12] if len(full_nifty_registry) >= 12 else full_nifty_registry,
            "MIDCAP": fallback_midcaps,
            "NIFTY": fallback_nifty_index
        }

        combined_tickers_set = set(["USDINR=X"])
        for assets_list in universes_pool.values():
            combined_tickers_set.update(assets_list)
        all_unique_tickers = list(combined_tickers_set)

        start_dt = pd.to_datetime(start_date)
        download_padding = int(macro_lookback * 31) + 90
        calculated_start = (start_dt - datetime.timedelta(days=download_padding)).strftime('%Y-%m-%d')

        print(f"📡 Downloader active: Fetching global market master data once from {calculated_start} to {end_date}...")
        raw_download = yf.download(all_unique_tickers, start=calculated_start, end=end_date, interval="1d",
                                   progress=False)
        master_historical_prices = raw_download['Close'] if 'Close' in raw_download else raw_download
        master_historical_prices = master_historical_prices.ffill().bfill()

        from ai.gemini_provider import GeminiModelProvider
        from ai.openai_provider import OpenAIModelProvider

        # Soft validation blocks to guarantee code safety limits
        gemini_client = GeminiModelProvider(api_key=api_token) if (api_token and not "Actual" in api_token) else None
        openai_client = OpenAIModelProvider(api_key=openai_token) if openai_token.startswith("sk-") else None

        # FIXED: Enforced a guaranteed instantiation array fallback pass for AI modules list keys
        analysts_pool = {
            "TECHNICAL_ONLY": [TechnicalAnalystAgent()],
            "FUNDAMENTAL": [FundamentalAnalystAgent()],
            "NEWS_KEYWORD": [NewsAnalystAgent(ai_provider=None)],
            "MACRO": [MacroAnalystAgent()],
            "GEMINI_AI": [NewsAnalystAgent(ai_provider=gemini_client)],
            "CHATGPT_AI": [NewsAnalystAgent(ai_provider=openai_client)]
        }

        os.makedirs(self.reports_dir, exist_ok=True)

        with open(self.summary_matrix_path, mode='w', newline='') as file:
            csv.writer(file).writerow(
                ["Label", "Zone", "Strategy", "Universe", "Analyst_Layer", "Net_Return_Pct", "Sharpe_Ratio",
                 "Max_Drawdown_Pct", "Taxes_Paid_INR"])

        experiment_count = 0
        for s_name, s_plugin in strategies_pool.items():
            for u_name, assets_pool in universes_pool.items():
                for a_name, active_analyst_list in analysts_pool.items():
                    experiment_count += 1
                    run_label = f"RUN_{s_name}_{u_name}_{a_name}"
                    run_ledger_file = os.path.join(current_pkg_dir, f"backtest_ledger_{run_label}.csv")

                    print(f"\n⚡ Processing Combinatorial Experiment Matrix Loop #{experiment_count}...")
                    print(f"   ➔ [Strategy: {s_name}] | [Universe: {u_name}] | [Reasoning Layer: {a_name}]")

                    runtime_payload = {
                        "start_date": start_date, "end_date": end_date, "initial_budget": initial_budget,
                        "tech_lookback": tech_lookback, "macro_lookback": macro_lookback,
                        "rebalance_days": rebalance_interval_days, "max_tickers": 4, "experiment_label": run_label,
                        "s_name": s_name, "u_name": u_name, "a_name": a_name
                    }

                    QuantitativeMathEngine.run_single_simulation_safely(
                        run_label=run_label, market_zone=market_zone, s_plugin=s_plugin,
                        active_analyst_list=active_analyst_list, assets_pool=assets_pool,
                        preloaded_data=master_historical_prices, runtime_payload=runtime_payload,
                        ledger_file=run_ledger_file, summary_matrix_path=self.summary_matrix_path
                    )

        print("\n📊 Strategy grid calculation loop finished. Rendering visual components...")
        QuantitativeMathEngine.generate_isolated_analyst_diagrams(
            self.summary_matrix_path, self.reports_dir, initial_budget, end_date, current_pkg_dir
        )

        df_matrix = pd.read_csv(self.summary_matrix_path)
        if not df_matrix.empty:
            print("🏁 Execution complete. Generating meta-reasoning optimizations maps...")
            advisor = SelfAnalysisDecisionEngine(summary_matrix_path=self.summary_matrix_path)
            advisor.discover_optimal_configuration()


if __name__ == "__main__":
    engine = QuantitativeDiscoveryEngine()
    engine.execute_grid_search()
