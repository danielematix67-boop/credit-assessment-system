from unittest.mock import MagicMock, patch

from src.llm.gemini_client import GeminiClient

# ============================================================
# Test data
# ============================================================

DEFAULT_MODEL = "gemini-3.5-flash"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_OUTPUT_TOKENS = 8192


# ============================================================
# Initialization
# ============================================================


def test_gemini_client_initializes_with_api_key():
    mock_client = MagicMock()

    with patch.dict(
        "os.environ",
        {"GEMINI_API_KEY": "test-api-key"},
    ):
        with patch(
            "src.llm.gemini_client.genai.Client",
            return_value=mock_client,
        ) as client_class:
            client = GeminiClient()

    client_class.assert_called_once_with(
        api_key="test-api-key",
    )

    assert client.model == DEFAULT_MODEL
    assert client.temperature == DEFAULT_TEMPERATURE
    assert client.max_output_tokens == DEFAULT_MAX_OUTPUT_TOKENS

    assert client.client is mock_client


def test_gemini_client_initializes_with_custom_configuration():
    mock_client = MagicMock()

    with patch(
        "src.llm.gemini_client.genai.Client",
        return_value=mock_client,
    ):
        client = GeminiClient(
            api_key="custom-key",
            model="custom-model",
            temperature=0.0,
            max_output_tokens=4096,
        )

    assert client.model == "custom-model"
    assert client.temperature == 0.0
    assert client.max_output_tokens == 4096



def test_gemini_client_requires_api_key():
    with patch.dict(
        "os.environ",
        {},
        clear=True,
    ):
        try:
            GeminiClient()

        except ValueError as error:
            assert "Gemini API key not configured" in str(error)

        else:
            raise AssertionError("Expected ValueError when API key is missing")


# ============================================================
# Generation
# ============================================================


def test_gemini_client_generates_response():
    response = MagicMock()
    response.text = "CRITICAL assessment identified."

    mock_client = MagicMock()

    mock_client.models.generate_content.return_value = response

    with patch(
        "src.llm.gemini_client.genai.Client",
        return_value=mock_client,
    ):
        client = GeminiClient(
            api_key="test-api-key",
            model="test-model",
        )

        result = client.generate(
            "Assess this credit position.",
        )

    assert result == "CRITICAL assessment identified."

    mock_client.models.generate_content.assert_called_once()


def test_gemini_client_passes_generation_configuration():
    response = MagicMock()
    response.text = "Generated response."

    mock_client = MagicMock()

    mock_client.models.generate_content.return_value = response

    with patch(
        "src.llm.gemini_client.genai.Client",
        return_value=mock_client,
    ):
        client = GeminiClient(
            api_key="test-api-key",
            model="test-model",
            temperature=0.1,
            max_output_tokens=4096,
        )

        client.generate(
            "Generate executive summary.",
        )

    _, kwargs = mock_client.models.generate_content.call_args

    assert kwargs["model"] == "test-model"
    assert kwargs["contents"] == ("Generate executive summary.")

    config = kwargs["config"]

    assert config.temperature == 0.1
    assert config.max_output_tokens == 4096


def test_gemini_client_rejects_empty_response():
    response = MagicMock()
    response.text = None

    mock_client = MagicMock()

    mock_client.models.generate_content.return_value = response

    with patch(
        "src.llm.gemini_client.genai.Client",
        return_value=mock_client,
    ):
        client = GeminiClient(
            api_key="test-api-key",
        )

        try:
            client.generate(
                "Generate text",
            )

        except ValueError as error:
            assert "Gemini returned an empty response" in str(error)

        else:
            raise AssertionError("Expected ValueError for empty response")
