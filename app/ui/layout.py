import streamlit as st


def render_header() -> None:
    """Render the compact application header."""
    st.title("Credit Assessment System")
    st.markdown(
        """
        <div class="app-subtitle">
            Deterministic credit-quality assessment with controlled AI-assisted reporting.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Render the application footer."""
    st.markdown(
        """
        <div class="footer">
            Credit Assessment System · Deterministic decision engine with controlled AI-assisted reporting.
            <br>
            Demo scenarios provide input data only. The LLM does not determine assessment status,
            rule severity, thresholds, or credit decisions; it only supports executive narrative generation.
        </div>
        """,
        unsafe_allow_html=True,
    )
