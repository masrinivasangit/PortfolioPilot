# portfolio/risk.py
class PortfolioRiskManager:
    def __init__(self, max_concentration: float = 0.25, max_tolerated_drawdown: float = -0.10):
        self.max_concentration = max_concentration
        self.tolerated_dd = max_tolerated_drawdown

    def inspect_order_safety(self, proposed_allocation: float, total_capital: float) -> bool:
        if total_capital <= 0: return False
        return (proposed_allocation / total_capital) <= self.max_concentration

    def adjust_risk_profile(self, historic_drawdown: float) -> float:
        """
        SELF-ANALYSIS GATEway: Dynamically scales down allocation size if
        drawdown limits are breached during simulation testing.
        """
        if historic_drawdown < self.tolerated_dd:
            # Overextended risk detected -> Enforce a strict 50% cash preservation buffer
            return 0.50
        return 1.0
