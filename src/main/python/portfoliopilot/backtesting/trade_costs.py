# backtesting/trade_costs.py
from backtesting.protocols import BaseFrictionEngine


class GlobalFrictionAccountingEngine(BaseFrictionEngine):
    def __init__(self, region: str = "IN"):
        self.region = region.upper()

    def calculate_trade_leakage(self, ticker: str, trade_value: float, action: str) -> float:
        action = action.upper()
        if self.region == "IN" or ticker.endswith(".NS"):
            # Discount Brokerage: 0.03% or ₹20 (whichever is lower)
            brokerage = min(20.0, trade_value * 0.0003)
            exchange_fees = trade_value * 0.0000322
            stamp_duty = trade_value * 0.00015 if action == "BUY" else 0.0

            # DELIVERY STT OVERHEAD: 0.1% on BOTH entry and exit execution trades
            stt = trade_value * 0.001
            gst = (brokerage + exchange_fees) * 0.18

            # FLAT DP CHARGE GATEWAY: CDSL/NSDL processing fee applied only on sell actions
            dp_fee = 15.93 if action == "SELL" else 0.0

            return brokerage + exchange_fees + stamp_duty + stt + gst + dp_fee

        elif self.region == "US" or ("." not in ticker):
            return min(5.0, max(0.5, trade_value * 0.0001))

        return trade_value * 0.0015

    def calculate_capital_gains_tax(self, buy_date, sell_date, buy_price: float, sell_price: float,
                                    shares: int) -> float:
        profit = (sell_price - buy_price) * shares
        if profit <= 0:
            return 0.0

        hold_days = (sell_date - buy_date).days
        if self.region == "IN":
            # Realized execution timeframe boundary checkpoint window
            if hold_days <= 365:
                return profit * 0.20  # Short-Term Capital Gains (STCG)
            return profit * 0.125  # Long-Term Capital Gains (LTCG)

        return profit * 0.15
