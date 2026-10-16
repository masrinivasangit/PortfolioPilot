# strategies/options.py
import pandas as pd
from backtesting.protocols import BaseInvestmentStrategy

class DerivativesOptionsStrategy(BaseInvestmentStrategy):
    def __init__(self):
        self.strategy_name = "Options_Protective_Collar"

    def generate_signals(self, historical_data: pd.DataFrame, pool_tickers: list, max_allowed: int) -> pd.DataFrame:
        """Scans underlying equity metrics to calculate protective option hedges."""
        derivative_signals = []
        for ticker in pool_tickers:
            if ticker not in historical_data.columns:
                continue

            prices = historical_data[ticker].dropna()
            if len(prices) < 2:
                continue

            historical_volatility = float(prices.pct_change().std())
            prices_array = prices.to_numpy()
            p_end = float(prices_array[-1])

            if historical_volatility > 0.01:
                estimated_option_premium = p_end * 0.015
                derivative_signals.append({
                    'Ticker': ticker,
                    'Score': historical_volatility,  # Rank options by volatility protection priority
                    'Price': p_end + estimated_option_premium  # Adjusted underlying cost structure
                })

        if not derivative_signals:
            return pd.DataFrame()

        return pd.DataFrame(derivative_signals).sort_values(by='Score', ascending=False).head(max_allowed)
