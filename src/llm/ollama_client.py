from ollama import Client

from src.llm.client import LLMClient


class OllamaClient(LLMClient):
    """
    LLM client implementation for Ollama.

    The client is model-agnostic: the specific Ollama model
    is provided through configuration.
    """

    def __init__(
        self,
        model: str,
        host: str = "http://localhost:11434",
        temperature: float = 0.0,
        num_predict: int = 512,
    ) -> None:
        self.model = model
        self.host = host
        self.temperature = temperature
        self.num_predict = num_predict

        self.client = Client(
            host=host,
        )

    def generate(
        self,
        prompt: str,
    ) -> str:
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            stream=False,
            options={
                "temperature": self.temperature,
                "num_predict": self.num_predict,
            },
            think=False,
        )

        return response["response"]
