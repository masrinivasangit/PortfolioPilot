# signals.py
import pandas as pd


class MomentumSignalModule:
    """
    The Ticker Selection Sub-Tool.
    Modify or swap the logic inside this module later to experiment with custom strategies.
    """

    def __init__(self, name="Weekly_Momentum"):
        self.strategy_name = name

    def pick_top_tickers(self, historical_close_data: pd.DataFrame, pool_tickers: list,
                         max_allowed: int) -> pd.DataFrame:
        """
        Processes market data and extracts the best asset choices.
        Current Strategy: Absolute rolling performance over the lookback window.
        """
        rankings = []
        window = historical_close_data[pool_tickers].dropna()

        if len(window) < 2:
            return pd.DataFrame()

        for ticker in pool_tickers:
            if ticker not in window.columns:
                continue

            prices = window[ticker].dropna()
            if len(prices) < 2:
                continue

            p_start = prices.iloc[0]
            p_end = prices.iloc[-1]

            if p_start > 0:
                weekly_return = (p_end - p_start) / p_start
                rankings.append({
                    'Ticker': ticker,
                    'Return': weekly_return,
                    'Price': p_end
                })

        df_rankings = pd.DataFrame(rankings)
        if df_rankings.empty:
            return pd.DataFrame()

        top_picks = df_rankings.sort_values(by='Return', ascending=False).head(max_allowed)
        return top_picks
