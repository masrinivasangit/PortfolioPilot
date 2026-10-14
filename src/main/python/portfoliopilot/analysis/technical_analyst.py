import pandas as pd

class TechnicalAnalystAgent:
    def __init__(self):
        pass

    def compute_rsi(self, prices: pd.Series, window: int = 14) -> float:
        """Calculates Relative Strength Index to identify overbought/oversold states."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / (loss + 1e-9)
        return 100 - (100 / (1 + rs.iloc[-1])) if not gain.empty else 50.0
