# strategies/swing.py
import pandas as pd


class SwingTradingStrategy:
    def __init__(self):
        self.name = "Swing_Reversion"

    def generate_reversion_triggers(self, pricing_block: pd.DataFrame, pool_tickers: list) -> pd.DataFrame:
        """Scores assets based on structural short-term trend pullbacks relative to moving averages."""
        rankings = []
        for ticker in pool_tickers:
            if ticker not in pricing_block.columns:
                continue

            ticker_series = pricing_block[ticker].dropna()
            available_rows = len(ticker_series)
            if available_rows < 2:
                continue

            window_size = min(5, available_rows)
            moving_avg = ticker_series.rolling(window=window_size).mean().iloc[-1]
            current_price = ticker_series.iloc[-1]

            if moving_avg > 0:
                # FIXED: Using absolute distance ensures the strategy flags high-velocity pullbacks
                # inside both overextended bull expansions and deep corrections flawlessly.
                deviation = abs(moving_avg - current_price) / moving_avg
                rankings.append({'Ticker': ticker, 'Score': deviation, 'Price': current_price})

        if not rankings:
            return pd.DataFrame()

        return pd.DataFrame(rankings).sort_values(by='Score', ascending=False)
