from unittest.mock import MagicMock, patch

import pytest

from src.llm.ollama_client import OllamaClient


# ============================================================
# Test data
# ============================================================


DEFAULT_HOST = "http://localhost:11434"
CUSTOM_HOST = "http://custom-host:11434"

TEST_MODEL = "test-model"

DEFAULT_TEMPERATURE = 0.2
DEFAULT_NUM_PREDICT = 2048


# ============================================================
# Initialization
# ============================================================


@patch("src.llm.ollama_client.Client")
def test_ollama_client_initializes_with_default_configuration(
    mock_client,
):
    client = OllamaClient(
        model=TEST_MODEL,
    )

    assert client.model == TEST_MODEL
    assert client.host == DEFAULT_HOST

    assert client.temperature == DEFAULT_TEMPERATURE
    assert client.num_predict == DEFAULT_NUM_PREDICT

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

    assert client.host == CUSTOM_HOST

    mock_client.assert_called_once_with(
        host=CUSTOM_HOST,
    )


@patch("src.llm.ollama_client.Client")
def test_ollama_client_initializes_with_custom_generation_parameters(
    mock_client,
):
    client = OllamaClient(
        model=TEST_MODEL,
        temperature=0.1,
        num_predict=4096,
    )

    assert client.temperature == 0.1
    assert client.num_predict == 4096


@pytest.mark.parametrize(
    "model",
    [
        "qwen3:4b",
        "qwen2.5:3b",
        "llama3.2:3b",
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
    "prompt,response",
    [
        (
            "Test prompt",
            "Generated response.",
        ),
        (
            "Generate executive summary.",
            "Executive summary.",
        ),
        (
            "Rewrite assessment comment.",
            "Improved comment.",
        ),
    ],
)
@patch("src.llm.ollama_client.Client")
def test_ollama_client_generates_response_with_parameters(
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
        stream=False,
        options={
            "temperature": DEFAULT_TEMPERATURE,
            "num_predict": DEFAULT_NUM_PREDICT,
        },
        think=False,
    )


@pytest.mark.parametrize(
    "generated_text",
    [
        "Generated response.",
        "Long generated response with multiple sentences.",
        "",
        "123",
        "CRITICAL WARNING",
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

    result = client.generate(
        "Test prompt",
    )

    assert result == generated_text


@patch("src.llm.ollama_client.Client")
def test_ollama_client_passes_custom_generation_configuration(
    mock_client_class,
):
    mock_client = MagicMock()

    mock_client.generate.return_value = {
        "response": "Response",
    }

    mock_client_class.return_value = mock_client

    client = OllamaClient(
        model=TEST_MODEL,
        temperature=0.0,
        num_predict=8192,
    )

    client.generate(
        "Prompt",
    )

    mock_client.generate.assert_called_once_with(
        model=TEST_MODEL,
        prompt="Prompt",
        stream=False,
        options={
            "temperature": 0.0,
            "num_predict": 8192,
        },
        think=False,
    )


@patch("src.llm.ollama_client.Client")
def test_ollama_client_disables_reasoning_mode(
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

    client.generate(
        "Rewrite text",
    )

    _, kwargs = mock_client.generate.call_args

    assert kwargs["think"] is False


# ============================================================
# Error handling
# ============================================================


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("Service unavailable"),
        ValueError("Invalid response"),
        ConnectionError("Connection failed"),
        TimeoutError("Timeout"),
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

    with pytest.raises(type(error)):
        client.generate(
            "Test prompt",
        )


@patch("src.llm.ollama_client.Client")
def test_ollama_client_requires_response_field(
    mock_client_class,
):
    mock_client = MagicMock()

    mock_client.generate.return_value = {}

    mock_client_class.return_value = mock_client

    client = OllamaClient(
        model=TEST_MODEL,
    )

    with pytest.raises(KeyError):
        client.generate(
            "Test prompt",
        )


# ============================================================
# Client lifecycle
# ============================================================


@patch("src.llm.ollama_client.Client")
def test_ollama_client_reuses_same_client_instance(
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

    client.generate("First")
    client.generate("Second")

    mock_client_class.assert_called_once_with(
        host=DEFAULT_HOST,
    )

    assert mock_client.generate.call_count == 2