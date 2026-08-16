import os

from google import genai

from src.llm.client import LLMClient


class GeminiClient(LLMClient):

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3.5-flash",
    ):
        resolved_api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
        )

        if not resolved_api_key:
            raise ValueError(
                "Gemini API key not configured. "
                "Set GEMINI_API_KEY in the environment "
                "or provide it explicitly."
            )

        self.client = genai.Client(
            api_key=resolved_api_key,
        )

        self.model = model

    def generate(
        self,
        prompt: str,
    ) -> str:

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        text = response.text

        if text is None:
            raise ValueError(
                "Gemini returned an empty response"
            )

        return text