# backtesting/trade_costs.py
from backtesting.protocols import BaseFrictionEngine


class GlobalFrictionAccountingEngine(BaseFrictionEngine):
    def __init__(self, region: str = "IN"):
        self.region = region.upper()

    def calculate_trade_leakage(self, ticker: str, trade_value: float, action: str) -> float:
        action = action.upper()
        if self.region == "IN" or ticker.endswith(".NS"):
            brokerage = min(20.0, trade_value * 0.0005)
            exchange_fees = trade_value * 0.0000322
            gst = (brokerage + exchange_fees) * 0.18
            stt = trade_value * 0.001 if action == "SELL" else 0.0
            stamp_duty = trade_value * 0.00015 if action == "BUY" else 0.0
            return brokerage + exchange_fees + gst + stt + stamp_duty

        elif self.region == "US" or ("." not in ticker):
            # US Market: Capped clearing charges
            return min(5.0, max(1.0, trade_value * 0.0001))

        # Default global fallback cross-border tracking leakage
        return trade_value * 0.0020

    def calculate_capital_gains_tax(self, buy_date, sell_date, buy_price: float, sell_price: float,
                                    shares: int) -> float:
        profit = (sell_price - buy_price) * shares
        if profit <= 0:
            return 0.0

        hold_days = (sell_date - buy_date).days
        if self.region == "IN":
            # Indian FY24-25 Revised Tax Framework
            if hold_days <= 365:
                return profit * 0.20  # Short-Term Capital Gains (STCG)
            return profit * 0.125  # Long-Term Capital Gains (LTCG)

        # Standard Global Flat Withholding Reserve Template
        return profit * 0.15
