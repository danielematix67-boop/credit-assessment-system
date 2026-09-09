from typing import Any

import streamlit as st

from app.demo_scenarios import DEMO_SCENARIOS, build_demo_position
from app.ui.credit_position import build_credit_position_from_ui, build_scenario_data_table
from src.models.position import CreditPosition


def render_credit_data_source() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    """Render the credit position and information source used for monitoring."""
    st.subheader("Credit Position")
    st.caption("Select the position to be reviewed by the monitoring assessment.")

    input_mode = st.radio(
        "Input mode",
        options=["Demo Scenario", "Manual Input"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if input_mode == "Demo Scenario":
        return _render_demo_scenario()

    return _render_manual_input()


def _render_demo_scenario() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    scenario_name = st.selectbox(
        "Scenario",
        options=list(DEMO_SCENARIOS.keys()),
        index=0,
    )
    scenario = DEMO_SCENARIOS[scenario_name]

    st.caption(scenario["description"])

    try:
        position = build_demo_position(scenario_name)
    except Exception as error:
        st.error("Unable to construct the selected demo scenario.")
        st.exception(error)
        st.stop()

    st.markdown("**Financial information available for review**")
    st.dataframe(
        build_scenario_data_table(position),
        width="stretch",
        hide_index=True,
    )

    return position, None, "Demo Scenario", scenario_name


def _render_manual_input() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    st.caption("Enter the financial information available for the credit review.")

    position_data = build_credit_position_from_ui()
    provided_fields = sum(value is not None for value in position_data.values())
    total_fields = len(position_data)

    columns = st.columns(3)
    with columns[0]:
        st.metric("Fields", total_fields)
    with columns[1]:
        st.metric("Available", provided_fields)
    with columns[2]:
        st.metric("Missing", total_fields - provided_fields)

    return None, position_data, "Manual Input", None
