# strategies/long_term.py
import pandas as pd
from backtesting.protocols import BaseInvestmentStrategy

class LongTermValueStrategy(BaseInvestmentStrategy):
    def __init__(self):
        self.name = "Long_Term_Value"

    def generate_signals(self, historical_data: pd.DataFrame, pool_tickers: list, max_allowed: int) -> pd.DataFrame:
        """Scores assets based on steady, long-term multi-week upward support paths."""
        rankings = []
        for ticker in pool_tickers:
            if ticker not in historical_data.columns:
                continue

            prices = historical_data[ticker].dropna()
            if len(prices) < 12:  # Requires a solid 12-week data history
                continue

            p_old = prices.iloc[-12]
            p_current = prices.iloc[-1]

            if p_old > 0:
                long_term_growth = (p_current - p_old) / p_old
                volatility_drag = prices.pct_change().std()
                risk_adjusted_trend = long_term_growth / (volatility_drag + 1e-9)

                rankings.append({'Ticker': ticker, 'Score': risk_adjusted_trend, 'Price': p_current})

        if not rankings:
            return pd.DataFrame()

        return pd.DataFrame(rankings).sort_values(by='Score', ascending=False).head(max_allowed)
