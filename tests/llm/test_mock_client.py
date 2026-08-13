from src.llm.client import LLMClient
from src.llm.mock_client import MockLLMClient


def test_mock_llm_client_implements_llm_contract():

    client = MockLLMClient()

    assert isinstance(client, LLMClient)


def test_mock_llm_client_generates_default_text():

    client = MockLLMClient()

    result = client.generate("Test prompt")

    assert result == "CRITICAL assessment identified."


def test_mock_llm_client_generates_configured_text():

    client = MockLLMClient(
        response="Custom LLM response.",
    )

    result = client.generate("Test prompt")

    assert result == "Custom LLM response."