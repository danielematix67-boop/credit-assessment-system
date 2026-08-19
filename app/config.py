import os
from typing import Any

import streamlit as st


# ============================================================
# Environment Detection
# ============================================================

def is_streamlit_cloud() -> bool:
    """
    Detect whether the application is running on
    Streamlit Community Cloud.
    """

    runtime_env = os.getenv(
        "STREAMLIT_RUNTIME_ENV",
        "",
    ).lower()

    sharing_mode = os.getenv(
        "STREAMLIT_SHARING_MODE",
        "",
    ).lower()

    return (
        runtime_env in {
            "cloud",
            "community",
        }
        or sharing_mode == "streamlit"
    )


# ============================================================
# Secrets Helpers
# ============================================================

def get_secret(
    key: str,
    default: Any = None,
) -> Any:
    """
    Safely retrieve a Streamlit secret.
    """

    try:
        return st.secrets.get(
            key,
            default,
        )

    except Exception:
        return default


# ============================================================
# Gemini Configuration
# ============================================================

def get_gemini_api_key() -> str | None:
    """
    Retrieve the Gemini API key.

    Priority:
    1. Streamlit secrets
    2. Environment variable
    """

    secret_value = get_secret(
        "GEMINI_API_KEY",
        None,
    )

    if secret_value:
        return str(secret_value)

    environment_value = os.getenv(
        "GEMINI_API_KEY"
    )

    if environment_value:
        return environment_value

    return None


# ============================================================
# Ollama Configuration
# ============================================================

def get_ollama_configuration() -> tuple[str, str]:
    """
    Retrieve Ollama host and model configuration.

    Priority:
    1. Streamlit secrets [ollama] section
    2. Environment variables
    3. Local defaults
    """

    ollama_section: dict[str, Any] = {}

    try:
        ollama_section = dict(
            st.secrets.get(
                "ollama",
                {},
            )
        )

    except Exception:
        ollama_section = {}

    ollama_host = (
        ollama_section.get("host")
        or os.getenv("OLLAMA_HOST")
        or "http://localhost:11434"
    )

    ollama_model = (
        ollama_section.get("model")
        or os.getenv("OLLAMA_MODEL")
        or "qwen3:0.6b"
    )

    return (
        str(ollama_host),
        str(ollama_model),
    )


# ============================================================
# Reporting Modes
# ============================================================

def get_reporting_modes() -> list[str]:
    """
    Return the reporting modes available in the
    current execution environment.

    Local:
        Deterministic
        Gemini + Fallback
        Ollama + Fallback

    Streamlit Cloud:
        Deterministic
        Gemini + Fallback
    """

    if is_streamlit_cloud():
        return [
            "Deterministic",
            "Gemini + Fallback",
        ]

    return [
        "Deterministic",
        "Gemini + Fallback",
        "Ollama + Fallback",
    ]