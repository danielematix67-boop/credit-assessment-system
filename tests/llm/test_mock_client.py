import pytest

from src.llm.client import LLMClient
from src.llm.mock_client import MockLLMClient


def test_mock_llm_client_implements_llm_contract():
    client = MockLLMClient()

    assert isinstance(client, LLMClient)


def test_mock_llm_client_generates_default_text():
    client = MockLLMClient()

    result = client.generate("Test prompt")

    assert result == MockLLMClient.DEFAULT_RESPONSE


def test_mock_llm_client_generates_configured_text():
    client = MockLLMClient(
        response="Custom LLM response.",
    )

    result = client.generate("Test prompt")

    assert result == "Custom LLM response."


def test_mock_llm_client_stores_last_prompt():
    client = MockLLMClient()

    prompt = "Test prompt"

    client.generate(prompt)

    assert client.last_prompt == prompt


def test_mock_llm_client_raises_configured_error():
    error = RuntimeError("LLM service unavailable")

    client = MockLLMClient(
        error=error,
    )

    with pytest.raises(RuntimeError, match="LLM service unavailable"):
        client.generate("Test prompt")
