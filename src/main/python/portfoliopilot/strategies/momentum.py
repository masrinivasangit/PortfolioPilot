# strategies/momentum.py
import pandas as pd
from backtesting.protocols import BaseInvestmentStrategy

class MomentumSignalModule(BaseInvestmentStrategy):
    def generate_signals(self, historical_data: pd.DataFrame, pool_tickers: list, max_allowed: int) -> pd.DataFrame:
        rankings = []
        for ticker in pool_tickers:
            if ticker not in historical_data.columns: continue
            series = historical_data[ticker].dropna()
            if len(series) < 2: continue
            arr = series.to_numpy()
            p_start, p_end = float(arr[0]), float(arr[-1])
            if p_start > 0:
                rankings.append({'Ticker': ticker, 'Score': (p_end - p_start) / p_start, 'Price': p_end})
        if not rankings: return pd.DataFrame()
        return pd.DataFrame(rankings).sort_values(by='Score', ascending=False).head(max_allowed)
