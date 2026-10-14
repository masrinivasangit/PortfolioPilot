class TradeCostCalculator:
    def __init__(self, platform="DISCOUNT"):
        self.platform = platform

    def calculate_frictions(self, trade_value: float, volume_impact: float = 0.0005) -> float:
        """Computes structural drag (brokerage, fees, estimated slippage)."""
        brokerage = min(20.0, trade_value * 0.0005) if self.platform == "DISCOUNT" else 0.0
        regulatory_fees = trade_value * 0.0012  # Approximation of STT, GST, and stamp duties
        slippage_drag = trade_value * volume_impact
        return brokerage + regulatory_fees + slippage_drag
