from src.llm.client import LLMClient


class MockLLMClient(LLMClient):

    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return "Mock LLM response"