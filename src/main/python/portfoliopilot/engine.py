# engine.py
import configparser
import os
import csv
import yfinance as yf
import pandas as pd

# 1. Import the AI Layer
from ai.gemini_provider import GeminiModelProvider
from ai.openai_provider import OpenAIModelProvider

# 2. Import the Analyst Agents
from analysis.technical_analyst import TechnicalAnalystAgent
from analysis.fundamental_analyst import FundamentalAnalystAgent
from analysis.news_analyst import NewsAnalystAgent
from analysis.macro_analyst import MacroAnalystAgent

# 3. Import the Execution Strategies
from strategies.momentum import MomentumSignalModule
from strategies.swing import SwingTradingStrategy
from strategies.long_term import LongTermValueStrategy

# 4. Import Portfolio Management Constraints
from portfolio.risk import PortfolioRiskManager
from portfolio.optimizer import PortfolioWeightAllocator


class ModularPortfolioEngine:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.load_configuration()
        self.initialize_architecture()

    def load_configuration(self):
        self.config.read(self.config_path)
        self.country = self.config.get("MARKET_SETTINGS", "market_country", fallback="US").upper()
        self.start_date = self.config.get("BACKTEST_SETTINGS", "start_date", fallback="2026-01-01")
        self.end_date = self.config.get("BACKTEST_SETTINGS", "end_date", fallback="2026-06-30")
        self.initial_budget = self.config.getfloat("MARKET_SETTINGS", "total_budget", fallback=50000.00)

        # Architecture Switches from User Config Profile
        self.active_analyst_setting = self.config.get("MARKET_SETTINGS", "active_analyst", fallback="MOMENTUM").upper()
        self.llm_provider_setting = self.config.get("MARKET_SETTINGS", "active_llm_provider", fallback="GEMINI").upper()
        self.api_token = self.config.get("MARKET_SETTINGS", "ai_credential_token", fallback="")

    def initialize_architecture(self):
        print(f"⚙️ Initializing PortfolioPilot Infrastructure Components...")

        # A. Wire up the requested LLM Provider
        if self.llm_provider_setting == "GEMINI":
            self.ai_provider = GeminiModelProvider()
        else:
            self.ai_provider = OpenAIModelProvider()

        # B. Instantiate Analyst Agents and pass AI access when required
        self.tech_analyst = TechnicalAnalystAgent()
        self.fundamental_analyst = FundamentalAnalystAgent()
        self.news_analyst = NewsAnalystAgent(ai_provider=self.ai_provider)
        self.macro_analyst = MacroAnalystAgent()

        # C. Wire up Portfolio Management & Risk gates
        self.risk_manager = PortfolioRiskManager(max_concentration=0.25)
        self.weight_allocator = PortfolioWeightAllocator()

        # D. Match Core Strategy Routing
        if "SWING" in self.active_analyst_setting:
            self.strategy = SwingTradingStrategy()
            print("💎 Active Strategy Pipeline Router: [Swing Reversion Strategy]")
        elif "LONG" in self.active_analyst_setting:
            self.strategy = LongTermValueStrategy()
            print("💎 Active Strategy Pipeline Router: [Long Term Value Strategy]")
        else:
            self.strategy = MomentumSignalModule()
            print("💎 Active Strategy Pipeline Router: [Weekly Momentum Strategy]")

    def extract_custom_pools(self) -> dict:
        universes = {}
        # Checks configuration headers that have _TIER in their settings
        for section in self.config.sections():
            if section.endswith("_TIER"):
                tier_name = section.replace("_TIER", "")
                weight = self.config.getfloat(section, "weight")
                max_tickers = self.config.getint(section, "max_tickers")

                # Fallback to general list templates if source index targets Large Indices
                if self.config.get(section, "source_index", fallback="LARGE_INDEX") == "LARGE_INDEX":
                    if self.country == "IN":
                        pool = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS",
                                "BHARTIARTL.NS"]
                    else:
                        pool = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]
                else:
                    raw_pool = self.config.get(section, f"custom_pool_{self.country}", fallback="")
                    pool = [t.strip() for t in raw_pool.split(",") if t.strip()]

                universes[tier_name] = {"weight": weight, "max_tickers": max_tickers, "pool": pool}
        return universes

    def run_simulation(self):
        universes = self.extract_custom_pools()
        all_tickers = list(set([ticker for tier in universes.values() for ticker in tier["pool"]]))

        if not all_tickers:
            print("❌ Architecture Route Error: Zero active tickers discovered. Validate configuration tier keys.")
            return

        print(f"📡 Downloading historical tracking blocks for {len(all_tickers)} assets...")
        market_data = yf.download(all_tickers, start=self.start_date, end=self.end_date, interval="1d", progress=False)

        if market_data.empty or 'Close' not in market_data:
            print("❌ Data Acquisition Failure: Yahoo Finance API returned empty dataset matrices.")
            return

        close_prices = market_data['Close']
        trading_days = close_prices.dropna(how='all')

        current_cash = self.initial_budget
        active_portfolio = []  # Tracks active loop execution states

        output_dir = os.path.dirname(self.config_path)
        ledger_file = os.path.join(output_dir, "backtest_ledger.csv")

        with open(ledger_file, mode='w', newline='') as file:
            csv.writer(file).writerow(["Cycle_Num", "Date", "Ticker", "Asset_Tier", "Quantity", "Price", "Action"])

        print(f"📊 Running processing scans on {len(trading_days)} transaction horizons...")

        # --- End-To-End Orchestration Cycle Loop ---
        for idx in range(1, len(trading_days)):
            current_date = trading_days.index[idx]

            # 1. Deduces systemic market regime conditions
            regime = self.macro_analyst.generate_market_regime_flag(self.country)

            # 2. Strategy evaluation filtering block across tiers
            for tier_name, tier_settings in universes.items():
                tier_budget = current_cash * tier_settings["weight"]

                # Filter down pool using strategy modules
                eligible_tickers = [t for t in tier_settings["pool"] if t in trading_days.columns]

                # Execute Technical Indicators across our components
                rankings = []
                for ticker in eligible_tickers:
                    price_series = trading_days[ticker].iloc[:idx + 1]
                    if len(price_series) < 14: continue

                    # Compute technical and fundamental flags
                    rsi_val = self.tech_analyst.compute_rsi(price_series)

                    # Accumulate scoring metrics data structure frames
                    rankings.append({'Ticker': ticker, 'Price': price_series.iloc[-1], 'RSI': rsi_val})

                df_rankings = pd.DataFrame(rankings)
                if df_rankings.empty: continue

                # Sort or manage allocations utilizing weight modules
                allocations = self.weight_allocator.compute_share_bounds(df_rankings, tier_budget)

                for alloc in allocations:
                    tk = alloc['Ticker']
                    pr = alloc['Price']
                    sh = alloc['Shares']

                    # Risk manager concentration filter guard
                    if self.risk_manager.inspect_order_safety(sh * pr, self.initial_budget):
                        with open(ledger_file, mode='a', newline='') as file:
                            csv.writer(file).writerow([idx, current_date.date(), tk, tier_name, sh, pr, "BUY"])

        print(f"\n🏁 Run Simulation Execution Cycle Complete.")
        print(f"📄 Ledger metrics logged successfully to: {ledger_file}")
