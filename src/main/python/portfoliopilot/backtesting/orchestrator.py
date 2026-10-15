# backtesting/orchestrator.py
import os, csv, yfinance as yf, pandas as pd
from portfolio.risk import PortfolioRiskManager
from portfolio.optimizer import PortfolioWeightAllocator
from portfolio.rebalancing import PortfolioRebalanceController
from backtesting.backtest_engine import HistoricalSimulationEngine
from backtesting.performance_plotter import PortfolioPerformancePlotter
from data.news_data import NewsDataLoader
from data.fundamentals import FundamentalsDataLoader
from analysis.news_analyst import NewsAnalystAgent
from analysis.fundamental_analyst import FundamentalAnalystAgent


class BacktestOrchestrator:
    def __init__(self, settings: dict, config_sections):
        self.settings = settings
        self.config_sections = config_sections
        self.risk_manager = PortfolioRiskManager(0.25)
        self.rebalance_controller = PortfolioRebalanceController(0.05)
        self.news_loader = NewsDataLoader()

        ai_instance = None
        if settings.get("llm_provider") == "GEMINI" and settings.get("api_key"):
            from portfoliopilot.ai.gemini_provider import GeminiModelProvider
            ai_instance = GeminiModelProvider(api_key=settings["api_key"])

        self.news_analyst = NewsAnalystAgent(ai_provider=ai_instance)
        self.fundamental_loader = FundamentalsDataLoader()
        self.fundamental_analyst = FundamentalAnalystAgent()

        # Explicit instantiation of exact strategy modules matching your file tree definitions
        from strategies.momentum import MomentumSignalModule
        from strategies.swing import SwingTradingStrategy
        from strategies.long_term import LongTermValueStrategy
        from strategies.options import DerivativesOptionsStrategy

        self.momentum_module = MomentumSignalModule()
        self.swing_module = SwingTradingStrategy()
        self.long_term_module = LongTermValueStrategy()
        self.options_module = DerivativesOptionsStrategy()
        self.portfolio_optimizer = PortfolioWeightAllocator()

    def execute_simulation_timeline(self, raw_market_pool: list, ledger_file_path: str):
        print("📡 Downloading market data metrics for tracking timeline...")
        active_strategy_id = self.settings["active_analyst_id"]
        print(f"🎯 Activating Operational Strategy Route: [{active_strategy_id}]")

        all_assets = list(set(raw_market_pool + ["^BSESN"]))
        market_data = \
        yf.download(all_assets, start="2023-09-01", end=self.settings["end_date"], interval="1d", progress=False)[
            'Close']
        fridays = market_data[market_data.index.dayofweek == 4].dropna(subset=["^BSESN"])

        execution_fridays = fridays[fridays.index >= self.settings["start_date"]]
        current_cash = self.settings["initial_budget"]
        holdings_tracker = {}

        with open(ledger_file_path, mode='w', newline='') as file:
            csv.writer(file).writerow(
                ["Cycle_Num", "Date", "Ticker", "Asset_Tier", "Quantity", "Price", "Friction_Cost", "Action"])

        # RUN CHRONOLOGICAL TIMELINE LOOPS
        for i in range(len(execution_fridays) - 1):
            cycle_date = execution_fridays.index[i + 1]

            available_tickers = [t for t in raw_market_pool if t in fridays.columns]
            historical_slice = fridays[available_tickers][fridays.index <= cycle_date].tail(
                self.settings["tech_lookback"])

            # FIXED: Hardlocked clean object routing parameters to bypass structural lookups
            if active_strategy_id == "FUTURE_OPTIONS":
                strategy_picks = self.options_module.scan_derivative_hedges(historical_slice, available_tickers).head(3)
            elif active_strategy_id == "LONG_TERM_INVESTING":
                strategy_picks = self.long_term_module.filter_universe(
                    fridays[available_tickers][fridays.index <= cycle_date], available_tickers).head(3)
            elif active_strategy_id == "SWING_TRADING":
                strategy_picks = self.swing_module.generate_reversion_triggers(historical_slice,
                                                                               available_tickers).head(3)
            else:
                strategy_picks = self.momentum_module.pick_top_tickers(historical_slice, available_tickers, 3)

            if strategy_picks.empty:
                continue

            fused_rankings = []
            for _, pick in strategy_picks.iterrows():
                tk = pick['Ticker']
                base_score = float(pick['Score'])
                pr = float(pick['Price'])

                sentiment = 1.0 + self.news_analyst.analyze_headlines(self.news_loader.fetch_ticker_news(tk))
                health = self.fundamental_analyst.evaluate_health(self.fundamental_loader.fetch_company_metrics(tk))
                fused_score = abs(base_score) * sentiment * health
                fused_rankings.append({'Ticker': tk, 'Score': fused_score, 'Price': pr})

            fused_df = pd.DataFrame(fused_rankings)
            calculated_orders = self.portfolio_optimizer.compute_share_bounds(fused_df, current_cash * 0.3)

            for order in calculated_orders:
                tk, pr, sh = order['Ticker'], order['Price'], order['Shares']
                if current_cash >= (sh * pr):
                    current_cash -= (sh * pr)
                    holdings_tracker[tk] = {"shares": sh}
                    with open(ledger_file_path, mode='a', newline='') as file:
                        csv.writer(file).writerow([i + 1, cycle_date.date(), tk, "LARGE_CAP", sh, pr, 20.0, "BUY"])

        final_date = execution_fridays.index[-1]
        for tk, data in list(holdings_tracker.items()):
            if tk in fridays.columns:
                pr = float(fridays.loc[final_date, tk])
                with open(ledger_file_path, mode='a', newline='') as file:
                    csv.writer(file).writerow(
                        [999, final_date.date(), tk, "LARGE_CAP", data["shares"], pr, 20.0, "SELL"])

        print("🏁 System simulation loops completed safely.")
        analyzer = HistoricalSimulationEngine(self.settings["initial_budget"])
        analyzer.process_ledger_results(ledger_file_path=ledger_file_path)
        plotter = PortfolioPerformancePlotter(self.settings["initial_budget"])
        plotter.generate_equity_chart(ledger_file_path=ledger_file_path)
