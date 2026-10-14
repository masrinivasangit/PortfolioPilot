# strategies/momentum.py
import pandas as pd

class MomentumSignalModule:
    def __init__(self, name="Dynamic_Velocity_Momentum"):
        self.strategy_name = name

    def pick_top_tickers(self, historical_close_data: pd.DataFrame, pool_tickers: list, max_allowed: int) -> pd.DataFrame:
        """Calculates momentum trend acceleration safely across rolling vector structures."""
        rankings = []
        for ticker in pool_tickers:
            if ticker not in historical_close_data.columns:
                continue

            prices = historical_close_data[ticker].dropna()
            if len(prices) < 2:
                continue

            # Safe extraction of boundary elements as numeric floats
            p_start = float(prices.head(1).item())
            p_end = float(prices.tail(1).item())

            if p_start > 0:
                normalized_return = (p_end - p_start) / p_start
                rankings.append({
                    'Ticker': ticker,
                    'Score': normalized_return,
                    'Price': p_end
                })

        if not rankings:
            return pd.DataFrame()

        df_rankings = pd.DataFrame(rankings)
        return df_rankings.sort_values(by='Score', ascending=False).head(max_allowed)
