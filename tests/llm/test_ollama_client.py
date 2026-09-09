import inspect
from unittest.mock import MagicMock, patch

import pytest

from src.llm.ollama_client import OllamaClient

# ============================================================
# Test data
# ============================================================


DEFAULT_HOST = "http://localhost:11434"
CUSTOM_HOST = "http://custom-host:11434"

TEST_MODEL = "test-model"

CUSTOM_TEMPERATURE = 0.1
CUSTOM_NUM_PREDICT = 4096


# ============================================================
# Helpers
# ============================================================


def get_default_generation_parameters() -> tuple[float, int]:
    """
    Retrieve OllamaClient generation defaults directly from
    the constructor signature.

    This avoids duplicating implementation defaults in tests.
    """
    signature = inspect.signature(OllamaClient.__init__)

    temperature = signature.parameters["temperature"].default
    num_predict = signature.parameters["num_predict"].default

    return temperature, num_predict


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

    default_temperature, default_num_predict = get_default_generation_parameters()

    assert client.model == TEST_MODEL
    assert client.host == DEFAULT_HOST

    assert client.temperature == default_temperature
    assert client.num_predict == default_num_predict

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

    mock_client.assert_called_once_with(
        host=CUSTOM_HOST,
    )


@patch("src.llm.ollama_client.Client")
def test_ollama_client_initializes_with_custom_generation_parameters(
    mock_client,
):
    client = OllamaClient(
        model=TEST_MODEL,
        temperature=CUSTOM_TEMPERATURE,
        num_predict=CUSTOM_NUM_PREDICT,
    )

    assert client.temperature == CUSTOM_TEMPERATURE
    assert client.num_predict == CUSTOM_NUM_PREDICT


@pytest.mark.parametrize(
    "model",
    [
        "test-model",
        "local-model",
        "custom-model",
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
def test_ollama_client_generates_response_with_default_parameters(
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

    default_temperature, default_num_predict = get_default_generation_parameters()

    assert result == response

    mock_client.generate.assert_called_once_with(
        model=TEST_MODEL,
        prompt=prompt,
        stream=False,
        options={
            "temperature": default_temperature,
            "num_predict": default_num_predict,
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
        temperature=CUSTOM_TEMPERATURE,
        num_predict=CUSTOM_NUM_PREDICT,
    )

    client.generate(
        "Prompt",
    )

    mock_client.generate.assert_called_once_with(
        model=TEST_MODEL,
        prompt="Prompt",
        stream=False,
        options={
            "temperature": CUSTOM_TEMPERATURE,
            "num_predict": CUSTOM_NUM_PREDICT,
        },
        think=False,
    )


# ============================================================
# Generation behaviour
# ============================================================


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


@patch("src.llm.ollama_client.Client")
def test_ollama_client_disables_streaming(
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
        "Generate text",
    )

    _, kwargs = mock_client.generate.call_args

    assert kwargs["stream"] is False


@patch("src.llm.ollama_client.Client")
def test_ollama_client_passes_generation_options(
    mock_client_class,
):
    mock_client = MagicMock()

    mock_client.generate.return_value = {
        "response": "Response",
    }

    mock_client_class.return_value = mock_client

    client = OllamaClient(
        model=TEST_MODEL,
        temperature=CUSTOM_TEMPERATURE,
        num_predict=CUSTOM_NUM_PREDICT,
    )

    client.generate(
        "Generate text",
    )

    _, kwargs = mock_client.generate.call_args

    assert kwargs["options"] == {
        "temperature": CUSTOM_TEMPERATURE,
        "num_predict": CUSTOM_NUM_PREDICT,
    }


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
