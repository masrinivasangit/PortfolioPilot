# strategies/swing.py
import pandas as pd
from backtesting.protocols import BaseInvestmentStrategy

class SwingTradingStrategy(BaseInvestmentStrategy):
    def generate_signals(self, historical_data: pd.DataFrame, pool_tickers: list, max_allowed: int) -> pd.DataFrame:
        rankings = []
        for ticker in pool_tickers:
            if ticker not in historical_data.columns: continue
            series = historical_data[ticker].dropna()
            rows = len(series)
            if rows < 2: continue
            window = min(5, rows)
            moving_avg = series.rolling(window=window).mean().iloc[-1]
            current_price = series.iloc[-1]
            if moving_avg > 0:
                deviation = abs(moving_avg - current_price) / moving_avg
                rankings.append({'Ticker': ticker, 'Score': deviation, 'Price': current_price})
        if not rankings: return pd.DataFrame()
        return pd.DataFrame(rankings).sort_values(by='Score', ascending=False).head(max_allowed)
