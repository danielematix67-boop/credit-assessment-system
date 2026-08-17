from unittest.mock import MagicMock, patch

import pytest

from src.llm.ollama_client import OllamaClient


# ============================================================
# Test data
# ============================================================


DEFAULT_HOST = "http://localhost:11434"
CUSTOM_HOST = "http://custom-host:11434"
TEST_MODEL = "test-model"


# ============================================================
# Initialization
# ============================================================


@patch("src.llm.ollama_client.Client")
def test_ollama_client_initializes_with_default_host(
    mock_client,
):
    client = OllamaClient(
        model=TEST_MODEL,
    )

    assert client.model == TEST_MODEL
    assert client.host == DEFAULT_HOST
    assert client.client is mock_client.return_value

    mock_client.assert_called_once_with(
        host=DEFAULT_HOST,
    )


@patch("src.llm.ollama_client.Client")
def test_ollama_client_initializes_with_custom_host(
    mock_client,
):
    client = OllamaClient(
        model=TEST_MODEL,
        host=CUSTOM_HOST,
    )

    assert client.model == TEST_MODEL
    assert client.host == CUSTOM_HOST
    assert client.client is mock_client.return_value

    mock_client.assert_called_once_with(
        host=CUSTOM_HOST,
    )


@pytest.mark.parametrize(
    "model",
    [
        "model-a",
        "model-b",
        "local-model",
        "test-model",
    ],
)
@patch("src.llm.ollama_client.Client")
def test_ollama_client_preserves_configured_model(
    mock_client,
    model,
):
    client = OllamaClient(
        model=model,
    )

    assert client.model == model


# ============================================================
# Generation
# ============================================================


@pytest.mark.parametrize(
    "prompt, response",
    [
        (
            "Test prompt",
            "Generated response.",
        ),
        (
            "Generate an executive summary.",
            "Generated executive summary.",
        ),
        (
            "Summarise the assessment.",
            "Assessment summary.",
        ),
    ],
)
@patch("src.llm.ollama_client.Client")
def test_ollama_client_generates_response(
    mock_client_class,
    prompt,
    response,
):
    mock_client = MagicMock()

    mock_client.generate.return_value = {
        "response": response,
    }

    mock_client_class.return_value = mock_client

    client = OllamaClient(
        model=TEST_MODEL,
    )

    result = client.generate(prompt)

    assert result == response

    mock_client.generate.assert_called_once_with(
        model=TEST_MODEL,
        prompt=prompt,
    )


@pytest.mark.parametrize(
    "generated_text",
    [
        "Generated response.",
        "A longer generated response containing "
        "multiple words and sentences.",
        "ATTENTION",
        "",
        "123",
    ],
)
@patch("src.llm.ollama_client.Client")
def test_ollama_client_preserves_generated_text(
    mock_client_class,
    generated_text,
):
    mock_client = MagicMock()

    mock_client.generate.return_value = {
        "response": generated_text,
    }

    mock_client_class.return_value = mock_client

    client = OllamaClient(
        model=TEST_MODEL,
    )

    result = client.generate("Test prompt")

    assert result == generated_text


@patch("src.llm.ollama_client.Client")
def test_ollama_client_passes_configured_model_and_prompt(
    mock_client_class,
):
    mock_client = MagicMock()

    mock_client.generate.return_value = {
        "response": "Response",
    }

    mock_client_class.return_value = mock_client

    model = "configured-model"
    prompt = "configured prompt"

    client = OllamaClient(
        model=model,
    )

    client.generate(prompt)

    mock_client.generate.assert_called_once_with(
        model=model,
        prompt=prompt,
    )


# ============================================================
# Error handling
# ============================================================


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("Service unavailable"),
        ValueError("Invalid response"),
        ConnectionError("Connection failed"),
        TimeoutError("Request timed out"),
    ],
)
@patch("src.llm.ollama_client.Client")
def test_ollama_client_propagates_generation_errors(
    mock_client_class,
    error,
):
    mock_client = MagicMock()

    mock_client.generate.side_effect = error

    mock_client_class.return_value = mock_client

    client = OllamaClient(
        model=TEST_MODEL,
    )

    with pytest.raises(type(error), match=str(error)):
        client.generate("Test prompt")

    mock_client.generate.assert_called_once_with(
        model=TEST_MODEL,
        prompt="Test prompt",
    )


@patch("src.llm.ollama_client.Client")
def test_ollama_client_propagates_missing_response_error(
    mock_client_class,
):
    mock_client = MagicMock()

    mock_client.generate.return_value = {}

    mock_client_class.return_value = mock_client

    client = OllamaClient(
        model=TEST_MODEL,
    )

    with pytest.raises(KeyError):
        client.generate("Test prompt")


@pytest.mark.parametrize(
    "response",
    [
        {"unexpected": "value"},
        {"result": "value"},
        {"text": "value"},
    ],
)
@patch("src.llm.ollama_client.Client")
def test_ollama_client_requires_response_field(
    mock_client_class,
    response,
):
    mock_client = MagicMock()
    mock_client.generate.return_value = response

    mock_client_class.return_value = mock_client

    client = OllamaClient(
        model=TEST_MODEL,
    )

    with pytest.raises(KeyError):
        client.generate("Test prompt")


# ============================================================
# Client interaction
# ============================================================


@patch("src.llm.ollama_client.Client")
def test_ollama_client_uses_initialized_client(
    mock_client_class,
):
    mock_client = MagicMock()

    mock_client.generate.return_value = {
        "response": "Response",
    }

    mock_client_class.return_value = mock_client

    client = OllamaClient(
        model=TEST_MODEL,
    )

    assert client.client is mock_client

    client.generate("Test prompt")

    mock_client.generate.assert_called_once()


@patch("src.llm.ollama_client.Client")
def test_ollama_client_does_not_create_new_client_per_request(
    mock_client_class,
):
    mock_client = MagicMock()

    mock_client.generate.return_value = {
        "response": "Response",
    }

    mock_client_class.return_value = mock_client

    client = OllamaClient(
        model=TEST_MODEL,
    )

    client.generate("First prompt")
    client.generate("Second prompt")

    mock_client_class.assert_called_once_with(
        host=DEFAULT_HOST,
    )

    assert mock_client.generate.call_count == 2