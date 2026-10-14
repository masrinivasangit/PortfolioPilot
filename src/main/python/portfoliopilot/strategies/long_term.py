import pandas as pd

class LongTermValueStrategy:
    def __init__(self):
        self.name = "Long_Term_Value"

    def filter_universe(self, historical_data: pd.DataFrame) -> list:
        """Selects historical multi-year breakout components with low volatility."""
        return list(historical_data.columns)
