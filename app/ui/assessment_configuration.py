import streamlit as st


def render_assessment_configuration(reporting_mode: str, input_mode: str) -> bool:
    """Render the single action that starts the monitoring assessment."""
    st.divider()
    st.subheader("Run Monitoring Assessment")
    source_label = "Demo Scenario" if input_mode == "Demo Scenario" else "Manual Input"
    st.caption(f"Review source: **{source_label}**")
    return st.button("Run Assessment", type="primary", width="stretch")
