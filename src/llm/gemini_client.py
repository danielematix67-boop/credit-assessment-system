import os

from google import genai

from src.llm.client import LLMClient


class GeminiClient(LLMClient):

    def __init__(
        self,
        model: str = "gemini-3.5-flash",
    ):
        api_key = os.environ["GEMINI_API_KEY"]

        self.client = genai.Client(
            api_key=api_key,
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

        return response.text