import streamlit as st

from app.config import get_reporting_modes, is_streamlit_cloud


def render_sidebar() -> str:
    """Render the minimal configuration required to run an assessment."""
    reporting_modes = get_reporting_modes()

    with st.sidebar:
        st.title("Configuration")
        st.caption("Choose how the Executive Report should be generated.")

        reporting_mode = st.radio(
            "Reporting mode",
            options=reporting_modes,
            index=0,
        )

        st.divider()

        st.markdown("**Decision**")
        st.caption("The Rule Engine always determines the credit assessment.")

        st.markdown("**Report**")
        st.caption("Deterministic, Gemini or Ollama can generate the narrative.")

        st.markdown("**Fallback**")
        st.caption("If an LLM fails, the deterministic report is used automatically.")

        if is_streamlit_cloud() and "Ollama + Fallback" in reporting_modes:
            st.info("Ollama is not available in the cloud environment.")

    return reporting_mode
