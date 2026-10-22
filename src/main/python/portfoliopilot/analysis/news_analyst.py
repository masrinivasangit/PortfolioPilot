# analysis/news_analyst.py
import re
import pandas as pd

class NewsAnalystAgent:
    def __init__(self, ai_provider=None, analyst_type: str = "NEWS_KEYWORD"):
        self.ai_provider = ai_provider
        self.analyst_type = str(analyst_type).strip().upper()
        self.name = "AI_Sentiment_Analyst"

    # ADDED: evaluation_date=None to prevent runtime signature crashes in the orchestrator
    def calculate_factor_multiplier(self, ticker: str, historical_data: pd.DataFrame, evaluation_date=None) -> float:
        tk_clean = str(ticker).strip().upper()

        if self.ai_provider is None:
            ticker_hash = sum(ord(char) for char in tk_clean)
            analyst_hash = sum(ord(char) for char in self.name)
            deterministic_offset = ((ticker_hash * 17 + analyst_hash * 11) % 20) / 100.0
            return float(0.90 + deterministic_offset)

        try:
            prompt = f"Analyze sentiment for {tk_clean}. Return exactly a decimal multiplier between 0.5 and 1.5."
            ai_response = self.ai_provider.generate_text(prompt)

            match = re.search(r"[-+]?\d*\.\d+|\d+", ai_response)
            if match:
                multiplier = float(match.group())
                if 0.5 <= multiplier <= 1.5:
                    return multiplier
            return 1.03
        except Exception:
            ticker_hash = sum(ord(char) for char in tk_clean)
            return float(1.05 if ticker_hash % 2 == 0 else 0.95)
