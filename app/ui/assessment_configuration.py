import streamlit as st


def render_assessment_configuration(
    reporting_mode: str,
    input_mode: str,
) -> bool:
    """Render the final run control without duplicating sidebar configuration."""
    st.divider()
    st.subheader("Run Assessment")

    if input_mode == "Demo Scenario":
        source_label = "Demo Scenario"
    else:
        source_label = "Manual Input"

    st.caption(
        f"Input: **{source_label}** · Reporting: **{reporting_mode}**"
    )

    return st.button(
        "Run Assessment",
        type="primary",
        width="stretch",
    )
