import pandas as pd
import yfinance as yf

class DataStreamProvider:
    def __init__(self, config_parser, country):
        self.config = config_parser
        self.country = country.upper()

    def extract_tier_universes(self) -> dict:
        universes = {}
        for section in self.config.sections():
            if section.endswith("_TIER"):
                tier_name = section.replace("_TIER", "")
                weight = self.config.getfloat(section, "weight")
                max_tickers = self.config.getint(section, "max_tickers")

                if self.config.get(section, "source_index", fallback="") == "LARGE_INDEX":
                    if self.country == "IN":
                        try:
                            payload = pd.read_html('https://wikipedia.org')
                            pool = (payload[1]['Symbol'] + ".NS").tolist()
                        except Exception:
                            pool = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
                    else:
                        try:
                            payload = pd.read_html('https://wikipedia.org')
                            pool = payload[0]['Symbol'].str.replace('.', '-', regex=False).tolist()
                        except Exception:
                            pool = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"]
                else:
                    raw_pool = self.config.get(section, f"custom_pool_{self.country}", fallback="")
                    pool = [t.strip() for t in raw_pool.split(",") if t.strip()]

                universes[tier_name] = {"weight": weight, "max_tickers": max_tickers, "pool": pool}
        return universes

    def download_historical_closes(self, tickers: list, start: str, end: str) -> pd.DataFrame:
        print(f"📡 Downloading data infrastructure metrics for {len(tickers)} assets via Yahoo Finance...")
        market_data = yf.download(tickers, start=start, end=end, interval="1d", progress=False)['Close']
        # Filter for trading day structures (Fridays)
        return market_data[market_data.index.dayofweek == 4]
