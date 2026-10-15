# analysis/news_analyst.py

class NewsAnalystAgent:
    def __init__(self, ai_provider=None):
        # Accepts GeminiModelProvider or OpenAIModelProvider dynamically
        self.ai = ai_provider

    def analyze_headlines(self, news_items: list) -> float:
        """Routes text payloads through Gemini/ChatGPT to extract an institutional score."""
        if not news_items or self.ai is None:
            return 0.0  # Neutral default fallback

        # Construct an advanced structural prompt for the LLM agent
        headlines_text = "\n".join([f"- {item.get('title')}" for item in news_items])

        prompt = f"""
        You are an expert financial analyst. Analyze the following stock headlines and evaluate the consensus market sentiment.
        Respond with exactly ONE floating-point number between -1.0 (extremely negative/panic) and 1.0 (extremely positive/euphoric).
        Do not include any explanation, reasoning, or markdown formatting characters. Just output the raw number.

        Headlines to analyze:
        {headlines_text}
        """

        # Call Gemini or ChatGPT live
        ai_response = self.ai.prompt_inference(prompt)

        try:
            return float(ai_response)
        except ValueError:
            return 0.0  # Safe neutral score if AI outputs text instead of a number
