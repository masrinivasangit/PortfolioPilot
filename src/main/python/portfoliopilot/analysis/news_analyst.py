# analysis/news_analyst.py
import re
import pandas as pd


class NewsAnalystAgent:
    def __init__(self, ai_provider=None, analyst_type: str = "NEWS_KEYWORD"):
        self.ai_provider = ai_provider
        self.analyst_type = str(analyst_type).strip().upper()
        self.name = "AI_Sentiment_Analyst"
        self.sentiment_cache = {}

    def calculate_factor_multiplier(self, ticker: str, historical_data: pd.DataFrame, evaluation_date=None) -> float:
        tk_clean = str(ticker).strip().upper()
        date_str = str(evaluation_date.date()) if evaluation_date else "STATIC_DAY"
        cache_key = f"{tk_clean}_{date_str}"

        if cache_key in self.sentiment_cache:
            return self.sentiment_cache[cache_key]

        # 1. LOCAL DETERMINISTIC SENTIMENT EMULATOR
        # Combines the ticker name and date string to create a safe pseudo-random value
        string_seed = f"{tk_clean}_{date_str}"
        combined_hash = sum(ord(char) * (idx + 1) for idx, char in enumerate(string_seed))

        # Maps the hash to a clean variance spread between -0.4 and +0.4
        simulated_score = ((combined_hash % 81) - 40) / 100.0

        # 2. TRANSLATE TO ALIGN WITH STRATEGY RATIO LIMITS
        if simulated_score >= 0:
            multiplier = 1.0 + (simulated_score * 0.5)  # Max 1.20
        else:
            multiplier = 1.0 + (simulated_score * 0.7)  # Min 0.72

        final_multiplier = round(float(multiplier), 2)
        self.sentiment_cache[cache_key] = final_multiplier
        return final_multiplier
