# strategies/options.py
import pandas as pd


class DerivativesOptionsStrategy:
    def __init__(self):
        self.strategy_name = "Options_Protective_Collar"

    def scan_derivative_hedges(self, historical_data: pd.DataFrame, pool_tickers: list) -> pd.DataFrame:
        """
        Scans underlying equity metrics to calculate protective hedges.
        Flags high-volatility assets that require premium insurance option overlays.
        """
        derivative_signals = []
        for ticker in pool_tickers:
            if ticker not in historical_data.columns:
                continue

            prices = historical_data[ticker].dropna()
            # FIXED: Reduced boundary limit from 5 to 2 to support lower configuration lookbacks
            if len(prices) < 2:
                continue

            # Measure asset variance (implied volatility approximation)
            historical_volatility = float(prices.pct_change().std())

            # Used format-proof item position methods to extract clear scalar numbers
            prices_array = prices.to_numpy()
            p_start = float(prices_array.item(0))
            p_end = float(prices_array.item(-1))

            # Calibrated the daily volatility threshold to an institutional 1.0% layer
            if historical_volatility > 0.01:
                # Simulating a 5% out-of-the-money target strike floor option configuration
                simulated_strike_floor = p_end * 0.95
                estimated_option_premium = p_end * 0.015

                derivative_signals.append({
                    'Ticker': ticker,
                    'Score': historical_volatility,  # Rank options by volatility protection priority
                    'Price': p_end + estimated_option_premium  # Adjusted underlying cost structure
                })

        if not derivative_signals:
            return pd.DataFrame()

        return pd.DataFrame(derivative_signals).sort_values(by='Score', ascending=False)
