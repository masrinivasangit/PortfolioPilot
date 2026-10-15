# strategies/momentum.py
import pandas as pd

class MomentumSignalModule:
    def __init__(self, name="Dynamic_Velocity_Momentum"):
        self.strategy_name = name

    def pick_top_tickers(self, historical_close_data: pd.DataFrame, pool_tickers: list, max_allowed: int) -> pd.DataFrame:
        rankings = []
        for ticker in pool_tickers:
            if ticker not in historical_close_data.columns:
                continue
            ticker_series = historical_close_data[ticker].dropna()
            if len(ticker_series) < 2:
                continue
            prices_array = ticker_series.to_numpy()
            p_start, p_end = float(prices_array[0]), float(prices_array[-1])
            if p_start > 0:
                rankings.append({'Ticker': ticker, 'Score': (p_end - p_start) / p_start, 'Price': p_end})
        if not rankings:
            return pd.DataFrame()
        return pd.DataFrame(rankings).sort_values(by='Score', ascending=False).head(max_allowed)
