from src.llm.client import LLMClient


class MockLLMClient(LLMClient):

    def generate(self, prompt: str) -> str:
        return "Generated text"