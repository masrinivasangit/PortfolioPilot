import yfinance as yf

class NewsDataLoader:
    def __init__(self):
        pass

    def fetch_ticker_news(self, ticker: str) -> list:
        """Gathers recent market headlines and metadata for context analysis."""
        try:
            asset = yf.Ticker(ticker)
            news_stream = asset.news
            processed_news = []
            for item in news_stream:
                processed_news.append({
                    "title": item.get("title"),
                    "publisher": item.get("publisher"),
                    "link": item.get("link"),
                    "timestamp": item.get("providerPublishTime")
                })
            return processed_news
        except Exception:
            return []
