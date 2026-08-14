from unittest.mock import MagicMock, patch

from src.llm.gemini_client import GeminiClient


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

    assert client.model == "gemini-3.5-flash"
    assert client.client is mock_client


def test_gemini_client_generates_response():

    response = MagicMock()
    response.text = "CRITICAL assessment identified."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = response

    with patch.dict(
        "os.environ",
        {"GEMINI_API_KEY": "test-api-key"},
    ):
        with patch(
            "src.llm.gemini_client.genai.Client",
            return_value=mock_client,
        ):

            client = GeminiClient(model="test-model")

            result = client.generate(
                "Assess this credit position."
            )

    assert result == "CRITICAL assessment identified."

    mock_client.models.generate_content.assert_called_once_with(
        model="test-model",
        contents="Assess this credit position.",
    )