import streamlit as st


def render_assessment_configuration(reporting_mode: str, input_mode: str) -> bool:
    """Render the compact action bar that starts the monitoring assessment."""
    source_label = input_mode
    st.caption(f"Ready to assess · Source: **{source_label}**")
    return st.button("Run Assessment", type="primary", width="stretch")
