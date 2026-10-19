# main.py - PART 1
import configparser
import os
import csv
import sys
import datetime
import copy
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
from analysis.velocity_analyst import VelocityBreakoutAnalyst
from analysis.compounder_analyst import LongTermCompounderAnalyst


class QuantitativeDiscoveryEngine:
    def __init__(self):
        self.config_path = os.path.join(current_pkg_dir, "config.properties")
        self.summary_matrix_path = os.path.join(current_pkg_dir, "optimal_strategy_matrix.csv")
        self.reports_dir = os.path.join(current_pkg_dir, "reports")
        self.config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))

    def execute_grid_search(self):
        print("omsivayanama")
        print("==================================================================")
        print(" ✈️  LAUNCHING CONFIG-DRIVEN PORTFOLIO PILOT MATRIX ENGINE      ✈️ ")
        print("==================================================================")

        if not os.path.exists(self.config_path):
            print(f"❌ Critical Error: Configuration file not found at {self.config_path}")
            return

        self.config.read(self.config_path)

        market_zone = self.config.get("MARKET_SETTINGS", "market_country", fallback="IN").strip().upper()
        start_date = self.config.get("BACKTEST_SETTINGS", "start_date", fallback="2026-01-01").strip()
        end_date = self.config.get("BACKTEST_SETTINGS", "end_date", fallback="2026-06-30").strip()
        initial_budget = self.config.getfloat("MARKET_SETTINGS", "total_budget", fallback=100000.00)

        print(f"📋 Loaded Parameters: Horizon {start_date} to {end_date} | Budget: ₹{initial_budget:,.2f}")

        api_token = self.config.get("MARKET_SETTINGS", "ai_credential_token", fallback="").strip()
        openai_token = self.config.get("MARKET_SETTINGS", "openai_credential_token", fallback="").strip()

        tech_lookback_weeks = self.config.getint("ANALYST_LOOKBACK_SETTINGS", "technical_lookback_weeks", fallback=2)
        tech_lookback_days = max(10, tech_lookback_weeks * 5)
        macro_lookback = self.config.getint("ANALYST_LOOKBACK_SETTINGS", "macro_lookback_months", fallback=12)
        rebalance_interval_days = self.config.getint("SCHEDULE_SETTINGS", "rebalance_days", fallback=5)

        large_cap_pool_size = self.config.getint("LARGE_CAP_TIER", "pool_size", fallback=50)
        large_cap_max = self.config.getint("LARGE_CAP_TIER", "max_tickers", fallback=5)

        mid_cap_pool_size = self.config.getint("MID_CAP_TIER", "pool_size", fallback=50)
        mid_cap_max = self.config.getint("MID_CAP_TIER", "max_tickers", fallback=4)

        risky_pool_size = self.config.getint("RISKY_TIER", "pool_size", fallback=50)
        risky_max = self.config.getint("RISKY_TIER", "max_tickers", fallback=2)

        # MASTER REPOSITORIES
        strategies_blueprints_master = {
            "MOMENTUM": MomentumSignalModule,
            "SWING": SwingTradingStrategy,
            "LONG_TERM": LongTermValueStrategy,
            "OPTIONS": DerivativesOptionsStrategy
        }

        analysts_base_pool_master = {
            "QUANT_CORE_TREND": [TechnicalAnalystAgent(), MacroAnalystAgent()],
            "VALUATION_ALPHA": [FundamentalAnalystAgent(), MacroAnalystAgent()],
            "SENTIMENT_ROTATION": [NewsAnalystAgent(ai_provider=None, analyst_type="NEWS_KEYWORD"),
                                   TechnicalAnalystAgent()],
            "LTCG_COMPOUNDER": [LongTermCompounderAnalyst(), FundamentalAnalystAgent()],
            "HYBRID_INTELLIGENCE": [VelocityBreakoutAnalyst(), MacroAnalystAgent(), FundamentalAnalystAgent()]
        }

        # DYNAMIC PROPERTY EXTRACTION
        raw_strategies = self.config.get("MARKET_SETTINGS", "active_strategies", fallback="LONG_TERM, MOMENTUM")
        raw_analysts = self.config.get("MARKET_SETTINGS", "active_analysts", fallback="LTCG_COMPOUNDER, QUANT_CORE_TREND")

        configured_strategies = [s.strip().upper() for s in raw_strategies.split(",") if s.strip()]
        configured_analysts = [a.strip().upper() for a in raw_analysts.split(",") if a.strip()]

        strategies_blueprints = {}
        for s_key in configured_strategies:
            if s_key in strategies_blueprints_master:
                strategies_blueprints[s_key] = strategies_blueprints_master[s_key]
            else:
                print(f"⚠️ Warning: Configured strategy '{s_key}' not found in master blueprints mapping.")

        analysts_base_pool = {}
        for a_key in configured_analysts:
            if a_key in analysts_base_pool_master:
                analysts_base_pool[a_key] = analysts_base_pool_master[a_key]
            else:
                print(f"⚠️ Warning: Configured analyst framework '{a_key}' not found in master pool mappings.")

        if not strategies_blueprints:
            strategies_blueprints = {"LONG_TERM": LongTermValueStrategy}
        if not analysts_base_pool:
            analysts_base_pool = {"LTCG_COMPOUNDER": [LongTermCompounderAnalyst(), FundamentalAnalystAgent()]}

        print(f"🚀 Initializing Matrix Sweep: [{', '.join(strategies_blueprints.keys())}] x [{', '.join(analysts_base_pool.keys())}]")

        raw_large_caps = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "ITC.NS", "LT.NS",
                          "BHARTIARTL.NS", "AXISBANK.NS", "MARUTI.NS", "WIPRO.NS", "HINDUNILVR.NS", "KOTAKBANK.NS",
                          "BAJAJFINSV.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "M&M.NS", "TITAN.NS", "ULTRACEMCO.NS",
                          "NTPC.NS", "POWERGRID.NS", "HCLTECH.NS", "SUNPHARMA.NS", "TATASTEEL.NS", "ONGC.NS"]

        raw_mid_caps = ["TATAELXSI.NS", "KPITTECH.NS", "POLYCAB.NS", "DIXON.NS", "COFORGE.NS", "MAXHEALTH.NS",
                        "PERSISTENT.NS", "CONCOR.NS", "VOLTAS.NS", "CUMMINSIND.NS", "AUBANK.NS", "BANDHANBNK.NS",
                        "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BATAINDIA.NS", "BEL.NS", "HAL.NS", "MUTHOOTFIN.NS"]

        raw_risky_pool = ["YESBANK.NS", "PAYTM.NS", "NYKAA.NS", "POLICYBZR.NS", "IDEA.NS", "SUZLON.NS", "IREDA.NS",
                          "RVNL.NS", "IRFC.NS", "JIOFIN.NS", "PNB.NS", "UNIONBANK.NS", "IOB.NS"]

        large_weight = self.config.getfloat("LARGE_CAP_TIER", "weight", fallback=0.60)
        mid_weight = self.config.getfloat("MID_CAP_TIER", "weight", fallback=0.30)
        risky_weight = self.config.getfloat("RISKY_TIER", "weight", fallback=0.10)

        universes_pool = {
            "LARGE_CAP_TIER": {
                "pool": [str(t).upper() for t in raw_large_caps[:large_cap_pool_size]],
                "weight": large_weight, "max_tickers": large_cap_max
            },
            "MID_CAP_TIER": {
                "pool": [str(t).upper() for t in raw_mid_caps[:mid_cap_pool_size]],
                "weight": mid_weight, "max_tickers": mid_cap_max
            },
            "RISKY_TIER": {
                "pool": [str(t).upper() for t in raw_risky_pool[:risky_pool_size]],
                "weight": risky_weight, "max_tickers": risky_max
            }
        }

        combined_tickers_set = set(["USDINR=X", "^BSESN"])
        for tier_data in universes_pool.values():
            combined_tickers_set.update(tier_data["pool"])
        all_unique_tickers = list(combined_tickers_set)

        start_dt = pd.to_datetime(start_date)
        download_padding = int(macro_lookback * 31) + 90
        calculated_start = (start_dt - datetime.timedelta(days=download_padding)).strftime('%Y-%m-%d')

        print(f"📡 Downloader Active: Requesting {len(all_unique_tickers)} tickers from {calculated_start} to {end_date}...")
        raw_download = yf.download(all_unique_tickers, start=calculated_start, end=end_date, interval="1d", progress=False)

        if raw_download.empty:
            print("❌ Critical Error: Empty market pricing dataset returned.")
            return

        if isinstance(raw_download.columns, pd.MultiIndex):
            if 'Close' in raw_download.columns.get_level_values(0):
                master_historical_prices = raw_download['Close']
            else:
                master_historical_prices = raw_download.xs('Close', axis=1, level=0, drop_level=True)
        else:
            master_historical_prices = raw_download['Close'] if 'Close' in raw_download.columns else raw_download

        master_historical_prices = master_historical_prices.dropna(how='all', axis=1)
        if master_historical_prices.index.tz is not None:
            master_historical_prices.index = master_historical_prices.index.tz_localize(None)

        master_historical_prices = master_historical_prices.ffill().bfill()
        master_historical_prices.columns = [str(col).strip().upper() for col in master_historical_prices.columns]

        print(f"✅ Data Acquisition Complete! Loaded Pricing Shape: {master_historical_prices.shape}")
# main.py - PART 2
        gemini_active = api_token.startswith("AIza") and "YourActual" not in api_token
        openai_active = openai_token.startswith("sk-") and "YourActual" not in openai_token

        if gemini_active and "GEMINI_AI_TREND" in configured_analysts:
            from ai.gemini_provider import GeminiModelProvider
            analysts_base_pool["GEMINI_AI_TREND"] = [
                NewsAnalystAgent(ai_provider=GeminiModelProvider(api_key=api_token), analyst_type="GEMINI_AI"),
                MacroAnalystAgent()
            ]
            print("🧠 Multi-Agent Configuration Router: [GEMINI_AI Stack Activated]")

        if openai_active and "CHATGPT_AI_TREND" in configured_analysts:
            from ai.openai_provider import OpenAIModelProvider
            analysts_base_pool["CHATGPT_AI_TREND"] = [
                NewsAnalystAgent(ai_provider=OpenAIModelProvider(api_key=openai_token), analyst_type="CHATGPT_AI"),
                TechnicalAnalystAgent()
            ]
            print("🧠 Multi-Agent Configuration Router: [CHATGPT_AI Stack Activated]")

        os.makedirs(self.reports_dir, exist_ok=True)

        # Write clean table metrics header (overwrites old file traces completely)
        with open(self.summary_matrix_path, mode='w', newline='') as file:
            csv.writer(file).writerow(
                ["Label", "Zone", "Strategy", "Universe", "Analyst_Layer", "Net_Return_Pct", "Sharpe_Ratio",
                 "Max_Drawdown_Pct", "Taxes_Paid_INR"])

        experiment_count = 0
        for s_name, s_class in strategies_blueprints.items():
            for u_name, u_settings in universes_pool.items():
                for a_name, base_analyst_list in analysts_base_pool.items():
                    experiment_count += 1
                    run_label = f"RUN_{s_name}_{u_name}_{a_name}"
                    run_ledger_file = os.path.join(self.reports_dir, f"backtest_ledger_{run_label}.csv")

                    print(f"⚡ Simulating Tracking Thread #{experiment_count}: [Strategy: {s_name} | Universe: {u_name} | Analyst: {a_name}]")

                    fresh_strategy_instance = s_class()
                    isolated_analyst_list = copy.deepcopy(base_analyst_list)

                    for idx_plug, analyst_agent in enumerate(isolated_analyst_list):
                        unique_id_scalar = 0.05 * (idx_plug + 1) + (experiment_count * 0.01)
                        if hasattr(analyst_agent, 'set_tier_weight'):
                            analyst_agent.set_tier_weight(unique_id_scalar)
                        if hasattr(analyst_agent, 'name'):
                            analyst_agent.name = f"{analyst_agent.name}_{experiment_count}_{idx_plug}"

                    runtime_payload = {
                        "start_date": start_date,
                        "end_date": end_date,
                        "initial_budget": initial_budget,
                        "tech_lookback": tech_lookback_days,
                        "macro_lookback": macro_lookback,
                        "rebalance_days": rebalance_interval_days,
                        "max_tickers": u_settings["max_tickers"],
                        "tier_weight": u_settings["weight"],
                        "experiment_label": run_label,
                        "s_name": s_name,
                        "u_name": u_name,
                        "a_name": a_name,
                        "loop_sequence_id": int(experiment_count)
                    }

                    QuantitativeMathEngine.run_single_simulation_safely(
                        run_label=run_label,
                        market_zone=market_zone,
                        s_plugin=fresh_strategy_instance,
                        active_analyst_list=isolated_analyst_list,
                        assets_pool=u_settings["pool"],
                        preloaded_data=master_historical_prices,
                        runtime_payload=runtime_payload,
                        ledger_file=run_ledger_file,
                        summary_matrix_path=self.summary_matrix_path
                    )

        # CRITICAL PROTECTION CHECK: Deduplicate matrix fields natively before chart generations
        print("\n🧹 Executing structural matrix database deduplication pass...")
        if os.path.exists(self.summary_matrix_path):
            df_cleanup = pd.read_csv(self.summary_matrix_path)
            if not df_cleanup.empty:
                df_cleanup.columns = [c.strip() for c in df_cleanup.columns]
                df_cleanup.drop_duplicates(subset=["Label"], keep="first", inplace=True)
                df_cleanup.to_csv(self.summary_matrix_path, index=False)

        print("\n📊 Strategy grid calculation loop finished. Rendering isolated visualization layers...")
        QuantitativeMathEngine.generate_isolated_analyst_diagrams(
            self.summary_matrix_path,
            self.reports_dir,
            initial_budget,
            end_date,
            current_pkg_dir
        )

        df_matrix = pd.read_csv(self.summary_matrix_path)
        if not df_matrix.empty:
            print("🏁 Execution complete. Generating meta-reasoning advisor optimization report...")
            advisor = SelfAnalysisDecisionEngine(summary_matrix_path=self.summary_matrix_path)
            advisor.discover_optimal_configuration()


if __name__ == "__main__":
    engine = QuantitativeDiscoveryEngine()
    engine.execute_grid_search()
