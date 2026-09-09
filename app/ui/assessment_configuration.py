import streamlit as st

from app.ui.components import (
    reporting_mode_badge_kind,
    show_badge,
)


def render_assessment_configuration(
    reporting_mode: str,
    input_mode: str,
) -> bool:
    """
    Render the assessment configuration section.

    Returns:
        bool: True when the Run Assessment button is clicked.
    """

    st.divider()

    st.subheader("Assessment Configuration")

    configuration_col1, configuration_col2 = st.columns(2)

    # --------------------------------------------------------
    # Reporting Mode
    # --------------------------------------------------------

    with configuration_col1:
        st.caption("Reporting mode")

        show_badge(
            reporting_mode,
            reporting_mode_badge_kind(reporting_mode),
        )

    # --------------------------------------------------------
    # Input Source
    # --------------------------------------------------------

    with configuration_col2:
        if input_mode == "Demo Scenario":
            st.caption("Input source: **Demo Scenario**")

        else:
            st.caption("Input source: **Manual Input**")

    # --------------------------------------------------------
    # Run Assessment Button
    # --------------------------------------------------------

    return st.button(
        "Run Assessment",
        type="primary",
        width="stretch",
    )
