# strategies/swing.py
import pandas as pd

class SwingTradingStrategy:
    def __init__(self):
        self.name = "Swing_Reversion"

    def generate_reversion_triggers(self, pricing_block: pd.DataFrame, pool_tickers: list) -> pd.DataFrame:
        """Scores assets based on short-term oversold mean-reversion pullbacks."""
        rankings = []
        for ticker in pool_tickers:
            if ticker not in pricing_block.columns:
                continue

            ticker_series = pricing_block[ticker].dropna()
            if len(ticker_series) < 5:
                continue

            moving_avg = ticker_series.rolling(window=5).mean().iloc[-1]
            current_price = ticker_series.iloc[-1]

            if moving_avg > 0:
                reversion_score = (moving_avg - current_price) / moving_avg
                rankings.append({'Ticker': ticker, 'Score': reversion_score, 'Price': current_price})

        if not rankings:
            return pd.DataFrame()

        return pd.DataFrame(rankings).sort_values(by='Score', ascending=False)
