import pandas as pd

class PortfolioWeightAllocator:
    @staticmethod
    def compute_share_bounds(top_picks: pd.DataFrame, tier_cash_budget: float) -> list:
        """
        Calculates execution structures based on available capital allocations.
        """
        allocations = []
        if top_picks.empty:
            return allocations

        cash_per_stock = tier_cash_budget / len(top_picks)
        for _, pick in top_picks.iterrows():
            tk = pick['Ticker']
            pr = pick['Price']
            sh = int(cash_per_stock // pr)

            if sh > 0:
                allocations.append({
                    'Ticker': tk,
                    'Price': pr,
                    'Shares': sh
                })
        return allocations
