import streamlit as st


def render_assessment_configuration(reporting_mode: str, input_mode: str) -> bool:
    """Render the compact action bar that starts the monitoring assessment."""
    source_label = "Demo Scenario" if input_mode == "Demo Scenario" else "Manual Input"
    st.caption(f"Ready to assess · Source: **{source_label}**")
    return st.button("Run Assessment", type="primary", width="stretch")
