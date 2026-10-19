# portfolio/optimizer.py
import pandas as pd
import numpy as np

class PortfolioWeightAllocator:
    def __init__(self):
        self.name = "Resilient_Conviction_Weight_Allocator"

    def compute_share_bounds(self, rankings_df: pd.DataFrame, available_budget: float) -> list:
        if rankings_df.empty or available_budget <= 100.0:
            return []

        min_score = rankings_df["Score"].min()
        if min_score <= 0:
            rankings_df = rankings_df.copy()
            rankings_df["Score"] = rankings_df["Score"] - min_score + 0.01

        total_score_sum = rankings_df["Score"].sum()
        if total_score_sum <= 0:
            return []

        sorted_picks = rankings_df.sort_values(by="Score", ascending=False)
        orders = []

        # PASS 1: Calculate raw baseline proportional allocations
        for _, row in sorted_picks.iterrows():
            tk = row['Ticker']
            raw_pr = row['Price']
            pr = float(raw_pr.iloc[-1]) if isinstance(raw_pr, pd.Series) else float(raw_pr)

            if pr <= 0 or pd.isna(pr) or available_budget < pr:
                continue

            score_fraction = row['Score'] / total_score_sum
            allocated_cash = available_budget * score_fraction
            shares_to_buy = int(allocated_cash // pr)

            if shares_to_buy > 0:
                cost = shares_to_buy * pr
                if available_budget >= cost:
                    orders.append({'Ticker': tk, 'Price': pr, 'Shares': shares_to_buy, 'Score': row['Score']})
                    available_budget -= cost

        # PASS 2: Balanced Score-Weighted Cash Sweep Pass
        # Distributes residual budget sequentially across available assets based on rank priority
        if orders and available_budget > 100.0:
            orders.sort(key=lambda x: x['Score'], reverse=True)

            for order in orders:
                pr = order['Price']
                if available_budget >= pr:
                    order['Shares'] += 1
                    available_budget -= pr
                if available_budget < 100.0:
                    break

        return [{'Ticker': o['Ticker'], 'Price': o['Price'], 'Shares': o['Shares']} for o in orders if o['Shares'] > 0]
