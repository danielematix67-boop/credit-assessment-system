from src.llm.client import LLMClient


class MockLLMClient(LLMClient):

    DEFAULT_RESPONSE = "CRITICAL assessment identified."

    def __init__(
        self,
        response: str | None = None,
        error: Exception | None = None,
    ):
        self.response = response
        self.error = error
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt

        if self.error is not None:
            raise self.error

        if self.response is not None:
            return self.response

        return self.DEFAULT_RESPONSE