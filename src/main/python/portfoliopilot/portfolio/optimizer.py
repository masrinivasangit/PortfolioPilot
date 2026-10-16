# portfolio/optimizer.py
import pandas as pd


class PortfolioWeightAllocator:
    @staticmethod
    def compute_share_bounds(top_picks: pd.DataFrame, tier_cash_budget: float) -> list:
        """
        Calculates optimized share boundaries to ensure aggressive capital deployment velocity.
        """
        allocations = []
        if top_picks.empty or tier_cash_budget <= 0:
            return allocations

        cash_per_stock = tier_cash_budget / len(top_picks)
        for _, pick in top_picks.iterrows():
            tk = pick['Ticker']
            pr = pick['Price']

            # Extract clean raw target shares count
            sh = int(cash_per_stock // pr)

            # FIXED: Fractional remainder safety check avoids skipping premium assets entirely
            if sh == 0 and tier_cash_budget >= pr:
                sh = 1

            if sh > 0:
                allocations.append({
                    'Ticker': tk,
                    'Price': pr,
                    'Shares': sh
                })
        return allocations
