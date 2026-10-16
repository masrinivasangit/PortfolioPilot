# analysis/macro_analyst.py
import pandas as pd


class MacroAnalystAgent:
    def __init__(self):
        self.name = "Macro_Regime_Engine"

    def calculate_factor_multiplier(self, ticker: str, historical_data: pd.DataFrame) -> float:
        # Reference the benchmark index to gauge systemic risk regimes
        benchmark = "^BSESN" if "^BSESN" in historical_data.columns else historical_data.columns[0]
        index_prices = historical_data[benchmark].dropna()

        if len(index_prices) < 20:
            return 1.0

        short_ma = index_prices.rolling(window=5).mean().iloc[-1]
        long_ma = index_prices.rolling(window=20).mean().iloc[-1]

        # Bullish Crossover: Market is healthy, amplify buy signal stability
        if short_ma >= long_ma:
            return 1.15
        else:
            # Bearish Market Regime: Enforce defensive capital preservation limits
            return 0.60
