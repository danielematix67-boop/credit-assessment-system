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
    ) -> None:
        self.model = model
        self.host = host
        self.client = Client(host=host)

    def generate(
        self,
        prompt: str,
    ) -> str:
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
            )

            generated_text = response["response"]

            print("=" * 60)
            print("OLLAMA RESPONSE")
            print(f"Model: {self.model}")
            print(f"Response type: {type(response)}")
            print("Generated text:")
            print(repr(generated_text))
            print("=" * 60)

            return generated_text

        except Exception as error:
            print("=" * 60)
            print("OLLAMA ERROR")
            print(f"Error type: {type(error).__name__}")
            print(f"Error message: {error}")
            print("=" * 60)

            raise