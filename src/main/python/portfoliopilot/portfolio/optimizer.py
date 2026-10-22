# portfolio/optimizer.py
import pandas as pd
import numpy as np
from backtesting.trade_costs import GlobalFrictionAccountingEngine


class PortfolioWeightAllocator:
    def __init__(self, region: str = "IN"):
        self.friction_calculator = GlobalFrictionAccountingEngine(region=region)

    def generate_optimal_allocations(self, sorted_picks: pd.DataFrame, available_budget: float,
                                     max_allowed: int) -> list:
        """Maintains signature parity for secondary execution engines."""
        return self.compute_share_bounds(sorted_picks, available_budget)

    def compute_share_bounds(self, sorted_picks: pd.DataFrame, available_budget: float, *args, **kwargs) -> list:
        """
        FIXED ORCHESTRATOR PATHWAY: This is the active method executing inside orchestrator.py.
        Processes proportional cash allocations, applies fractional force-buys, and
        guards capital from leakages via the 0.25% Dynamic Friction Buffer Filter.
        """
        if sorted_picks.empty:
            return []

        orders = []
        total_score_sum = sorted_picks['Score'].sum()
        if total_score_sum <= 0:
            return []

        # Iterate through strategy targets to determine execution share limits
        for _, row in sorted_picks.iterrows():
            tk = row['Ticker']
            raw_pr = row['Price']
            pr = float(raw_pr.iloc[-1]) if isinstance(raw_pr, pd.Series) else float(raw_pr)

            if pr <= 0 or pd.isna(pr) or available_budget < pr:
                continue

            score_fraction = row['Score'] / total_score_sum
            allocated_cash = available_budget * score_fraction
            shares_to_buy = int(allocated_cash // pr)

            # Proportional Force-Buy Trigger for concentrated alpha stability
            if shares_to_buy == 0 and available_budget >= pr:
                shares_to_buy = 1

            if shares_to_buy > 0:
                position_value = shares_to_buy * pr

                # DYNAMIC FRICTION BUFFER FILTER: Predict trade leakage cost prior to execution
                estimated_friction = self.friction_calculator.calculate_trade_leakage(
                    ticker=tk,
                    trade_value=position_value,
                    action="BUY"
                )

                # Institutional Gate: If transaction costs consume > 0.25% of the position value, skip it!
                friction_ratio = estimated_friction / position_value
                if friction_ratio > 0.0025:
                    continue  # Drops high-churn, inefficient trades immediately

                if available_budget >= (position_value + estimated_friction):
                    # Aligned perfectly to unpack directly into: tk, pr_raw, sh = order['Ticker'], order['Price'], order['Shares']
                    orders.append({
                        'Ticker': tk,
                        'Price': pr,
                        'Shares': shares_to_buy,
                        'Friction_Cost': estimated_friction
                    })
                    available_budget -= (position_value + estimated_friction)

        return orders
