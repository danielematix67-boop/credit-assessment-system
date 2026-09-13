import os

from google import genai
from google.genai import types

from src.llm.client import LLMClient


class GeminiClient(LLMClient):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3.5-flash",
        temperature: float = 0.1,
        max_output_tokens: int = 8192,
    ) -> None:
        resolved_api_key = api_key or os.getenv("GEMINI_API_KEY")

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
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    def generate(
        self,
        prompt: str,
    ) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                thinking_config=types.ThinkingConfig(
                    thinking_level="minimal",
                    include_thoughts=False,
                ),
            ),
        )

        text = response.text

        if text is None:
            raise ValueError("Gemini returned an empty response")

        return text
