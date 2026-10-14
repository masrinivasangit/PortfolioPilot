import yfinance as yf
import pandas as pd

class FundamentalsDataLoader:
    def __init__(self):
        pass

    def fetch_company_metrics(self, ticker: str) -> dict:
        """Fetches fundamental metrics for valuation and risk profiling."""
        try:
            asset = yf.Ticker(ticker)
            info = asset.info
            return {
                "ticker": ticker,
                "pe_ratio": info.get("trailingPE", None),
                "pb_ratio": info.get("priceToBook", None),
                "debt_to_equity": info.get("debtToEquity", None),
                "operating_margin": info.get("operatingMargins", None),
                "free_cashflow": info.get("freeCashflow", None)
            }
        except Exception as e:
            return {"ticker": ticker, "error": str(e)}
