from src.llm.client import LLMClient
from src.llm.openai_client import OpenAIClient


def test_openai_client_implements_llm_client_contract():

    client = OpenAIClient(
        api_key="test-key",
        model="test-model",
    )

    assert isinstance(client, LLMClient)