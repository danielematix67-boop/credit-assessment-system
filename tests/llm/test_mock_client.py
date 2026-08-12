from src.llm.client import LLMClient
from src.llm.mock_client import MockLLMClient


def test_mock_llm_client_implements_llm_contract():

    client = MockLLMClient()

    assert isinstance(client, LLMClient)


def test_mock_llm_client_generates_text():

    client = MockLLMClient()

    result = client.generate("Test prompt")

    assert result == "Generated text"