import streamlit as st


def render_header() -> None:
    """Render the application header."""

    st.title("Credit Assessment System")

    st.markdown(
        """
        <div class="app-subtitle">
            Deterministic credit-quality assessment with
            controlled, clearly-labelled AI-assisted reporting.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()


def render_footer() -> None:
    """Render the application footer."""

    st.markdown(
        """
        <div class="footer">
            Credit Assessment System · Deterministic decision engine
            with controlled, clearly-labelled AI-assisted reporting.
            <br>
            Demo scenarios provide input data only.
            The LLM does not determine assessment status,
            rule severity, thresholds, or credit decisions —
            it only phrases the executive summary, and every
            such section is marked with an 🤖 AI badge.
        </div>
        """,
        unsafe_allow_html=True,
    )
