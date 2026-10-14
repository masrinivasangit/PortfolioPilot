from portfoliopilot.ai.provider import BaseAIProvider

class GeminiModelProvider(BaseAIProvider):
    def prompt_inference(self, prompt: str) -> str:
        # standard initialization logic for google-genai client maps here
        return "Gemini inference complete."
