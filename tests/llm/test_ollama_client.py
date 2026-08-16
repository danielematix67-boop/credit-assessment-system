import pytest

from src.llm.client import LLMClient
from src.llm.ollama_client import OllamaClient


@pytest.mark.ollama
def test_ollama_client_implements_llm_client_contract():
    client = OllamaClient()

    assert isinstance(client, LLMClient)


@pytest.mark.ollama
def test_ollama_client_generates_response():
    client = OllamaClient()

    response = client.generate(
        "Write one concise sentence about credit risk."
    )

    assert isinstance(response, str)
    assert response.strip()


@pytest.mark.ollama
def test_ollama_client_generates_credit_risk_summary():
    client = OllamaClient()

    response = client.generate(
        "Write a concise professional credit-risk conclusion "
        "for a company with declining revenue and high leverage. "
        "Do not invent any additional facts."
    )

    assert isinstance(response, str)
    assert response.strip()
