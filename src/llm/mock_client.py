from src.llm.client import LLMClient


class MockLLMClient(LLMClient):

    def __init__(
        self,
        response: str = "CRITICAL assessment identified.",
    ):
        self.response = response
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response