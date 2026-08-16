from ollama import Client

from src.llm.client import LLMClient


class OllamaClient(LLMClient):
    """
    LLM client implementation for Ollama.

    Ollama is used as an alternative LLM provider to cloud-based
    clients such as Gemini.

    The client implements the common LLMClient interface, so the
    reporting layer remains independent from the underlying LLM
    provider.
    """

    def __init__(
        self,
        model: str = "qwen3:4b",
        host: str = "http://localhost:11434",
    ):
        self.model = model
        self.client = Client(host=host)

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate a response using the configured Ollama model.
        """

        response = self.client.generate(
            model=self.model,
            prompt=prompt,
        )

        return response["response"]