# analysis/fundamental_analyst.py
import pandas as pd

class FundamentalAnalystAgent:
    def __init__(self):
        self.name = "Fundamental_Financial_Expert"
        self.tier_weight = 0.33

    def set_tier_weight(self, weight: float):
        self.tier_weight = float(weight)

    # ADDED: evaluation_date=None pattern mapping interface alignment
    def calculate_factor_multiplier(self, ticker: str, historical_data: pd.DataFrame, evaluation_date=None) -> float:
        tk_clean = str(ticker).strip().upper()
        if tk_clean not in historical_data.columns:
            return 1.00

        prices = pd.Series(historical_data[tk_clean].values.flatten(), index=historical_data.index).dropna()
        if len(prices) < 5:
            return 1.00

        rolling_median = float(prices.rolling(window=min(len(prices), 20)).median().iloc[-1])
        current_price = float(prices.iloc[-1])

        weight_scalar = float(self.tier_weight) * 0.5

        if current_price <= rolling_median:
            return float(1.20 + weight_scalar)
        return float(0.80 - weight_scalar)
