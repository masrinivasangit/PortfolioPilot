class PortfolioRiskManager:
    def __init__(self, max_concentration: float = 0.25):
        self.max_concentration = max_concentration

    def inspect_order_safety(self, proposed_allocation: float, total_capital: float) -> bool:
        """Ensures no individual trade exceeds portfolio concentration thresholds."""
        if total_capital <= 0: return False
        return (proposed_allocation / total_capital) <= self.max_concentration
