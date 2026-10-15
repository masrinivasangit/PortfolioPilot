# analysis/macro_analyst.py
import pandas as pd


class MacroAnalystAgent:
    def __init__(self):
        self.name = "Secular_Macro_Regime_Engine"

    def determine_regime_safeguards(self, market_index_history: pd.DataFrame) -> dict:
        """
        Evaluates the broad market vector path over the configured macro lookback.
        Returns risk constraints (BULLISH = Full Speed, BEARISH = Accumulate Liquid Cash).
        """
        if market_index_history.empty or len(market_index_history) < 2:
            return {"regime": "BULLISH", "cash_buffer_modifier": 1.0}

        # Extract initial and final historical data points across macro lookback parameters
        old_val = float(market_index_history.iloc[0])
        current_val = float(market_index_history.iloc[-1])

        macro_return = (current_val - old_val) / old_val

        if macro_return < -0.05:
            # Under BEARISH regimes, system cuts spending budgets by 50% to shield active capital pools
            return {"regime": "BEARISH", "cash_buffer_modifier": 0.50}
        else:
            return {"regime": "BULLISH", "cash_buffer_modifier": 1.0}
