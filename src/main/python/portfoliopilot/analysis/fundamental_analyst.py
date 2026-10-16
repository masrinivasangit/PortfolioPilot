# analysis/fundamental_analyst.py
import pandas as pd
from data.fundamentals import FundamentalsDataLoader


class FundamentalAnalystAgent:
    def __init__(self):
        self.name = "Multi_Factor_Value_Evaluator"
        # Self-contained data loader instance to enforce clean encapsulation limits
        self.fundamental_loader = FundamentalsDataLoader()

    def calculate_factor_multiplier(self, ticker: str, historical_slice: pd.DataFrame) -> float:
        """
        Independently analyzes corporate financial statements and balance sheets.
        Returns a valuation factor multiplier score safely.
        """
        fundamental_metrics = self.fundamental_loader.fetch_company_metrics(ticker)

        if "error" in fundamental_metrics or not fundamental_metrics:
            return 1.0  # Safe neutral multiplier fallback

        score_modifier = 1.0

        # 1. BALANCE SHEET HEALTH SAFETY GATES
        d2e = fundamental_metrics.get("debt_to_equity", 50.0)
        op_margin = fundamental_metrics.get("operating_margin", 0.15)

        if d2e < 40.0:
            score_modifier += 0.1  # Reward low leverage structures
        elif d2e > 120.0:
            score_modifier -= 0.2  # Penalize heavy debt loads

        if op_margin > 0.22:
            score_modifier += 0.1  # Reward high cash generative machines

        # 2. P/E RATIO STRUCTURAL VALUATION GATES
        pe_ratio = fundamental_metrics.get("pe_ratio")
        if pe_ratio is not None:
            if pe_ratio <= 0:
                score_modifier = 0.1  # Discard companies losing money (Negative earnings)
            elif pe_ratio > 50.0:
                score_modifier *= 0.5  # Heavy 50% score cut for speculative bubbles
            elif pe_ratio > 30.0:
                score_modifier *= 0.8  # 20% haircut for premium overvalued metrics
            elif pe_ratio < 15.0:
                score_modifier *= 1.2  # 20% bonus incentive for deep value bargain stocks

        return min(max(score_modifier, 0.1), 1.5)
