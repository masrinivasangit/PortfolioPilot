# analysis/technical_analyst.py
import pandas as pd
import numpy as np


class TechnicalAnalystAgent:
    def __init__(self):
        self.name = "Technical_Indicator_Expert"

    def compute_rsi(self, price_series: pd.Series, period: int = 14) -> float:
        if len(price_series) < period + 1:
            return 50.0
        delta = price_series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if isinstance(rsi, pd.Series) else float(rsi)

    def calculate_factor_multiplier(self, ticker: str, historical_data: pd.DataFrame) -> float:
        if ticker not in historical_data.columns:
            return 1.0
        prices = historical_data[ticker].dropna()
        rsi = self.compute_rsi(prices)

        # Mean Reversion: Favor oversold assets (RSI < 40) by boosting their signal weight
        if rsi < 40:
            return 1.25
        elif rsi > 70:
            return 0.75
        return 1.0
