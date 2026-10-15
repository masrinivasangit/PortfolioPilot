# ai/gemini_provider.py
from google import genai
from portfoliopilot.ai.provider import BaseAIProvider

class GeminiModelProvider(BaseAIProvider):
    def __init__(self, api_key: str):
        super().__init__()
        # FIXED: Initializing the official unified GenAI Client structure
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-1.5-flash"

    def prompt_inference(self, prompt: str) -> str:
        """Sends news payloads to Gemini to analyze market sentiment."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            return "0.0"  # Safe neutral sentiment fallback if API drops out
