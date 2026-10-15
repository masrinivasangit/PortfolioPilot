# engine.py
import configparser
import os
from backtesting.orchestrator import BacktestOrchestrator


class ModularPortfolioEngine:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
        self.load_configuration()

    def load_configuration(self):
        self.config.read(self.config_path)
        self.country = self.config.get("MARKET_SETTINGS", "market_country", fallback="US").strip().upper()
        self.start_date = self.config.get("BACKTEST_SETTINGS", "start_date", fallback="2024-01-01").strip()
        self.end_date = self.config.get("BACKTEST_SETTINGS", "end_date", fallback="2024-06-30").strip()
        self.initial_budget = self.config.getfloat("MARKET_SETTINGS", "total_budget", fallback=50000.00)
        self.active_analyst_id = self.config.get("MARKET_SETTINGS", "active_analyst",
                                                 fallback="TECHNICAL_ANALYST").strip().upper()

        # Pull your new AI settings properties
        self.llm_provider = self.config.get("MARKET_SETTINGS", "active_llm_provider", fallback="NONE").strip().upper()
        self.api_key = self.config.get("MARKET_SETTINGS", "ai_credential_token", fallback="").strip()

        self.tech_lookback = self.config.getint("ANALYST_LOOKBACK_SETTINGS", "technical_lookback_weeks", fallback=4)
        self.macro_lookback = self.config.getint("ANALYST_LOOKBACK_SETTINGS", "macro_lookback_months", fallback=12)

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
        # Pack up runtime dictionary configurations cleanly
        runtime_settings = {
            "country": self.country, "start_date": self.start_date, "end_date": self.end_date,
            "initial_budget": self.initial_budget, "active_analyst_id": self.active_analyst_id,
            "tech_lookback": self.tech_lookback, "macro_lookback": self.macro_lookback,
            "llm_provider": self.llm_provider, "api_key": self.api_key
            # Inject AI values into orchestrator settings payload
        }

        for section in self.config.sections():
            if section.endswith("_TIER"):
                runtime_settings[f"{section}_weight"] = self.config.getfloat(section, "weight")
                runtime_settings[f"{section}_max_tickers"] = self.config.getint(section, "max_tickers")

        output_dir = os.path.dirname(self.config_path)
        ledger_file = os.path.join(output_dir, "backtest_ledger.csv")
        raw_market_pool = self.broad_market_data_pool()

        orchestrator = BacktestOrchestrator(settings=runtime_settings, config_sections=self.config.sections())
        orchestrator.execute_simulation_timeline(raw_market_pool=raw_market_pool, ledger_file_path=ledger_file)
