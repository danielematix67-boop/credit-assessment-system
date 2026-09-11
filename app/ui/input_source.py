import streamlit as st

from typing import Any

from app.demo_scenarios import DEMO_SCENARIOS, build_demo_position
from src.models.position import CreditPosition
from app.ui.input import build_credit_position_from_ui, display_position_table


_SCENARIO_GROUPS = {
    "1 · Baseline": ["01 · Baseline"],
    "2 · Customer Profile": ["02 · Customer Profile Risk"],
    "3 · Financial Analysis": [
        "03 · Revenue & Profitability Risk",
        "04 · Leverage & Interest Risk",
        "05 · Profitability Quality Risk",
    ],
    "4 · Behavioural Analysis": ["06 · Behavioural Risk"],
    "5 · Debt Sustainability": ["07 · Debt Sustainability Risk"],
    "6 · End-to-End / Data Quality": [
        "08 · Integrated Credit Stress",
        "09 · Data Availability",
    ],
}


def render_credit_data_source() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    """Render the credit position and its information source."""
    st.subheader("Credit Position")

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
    group_name = st.selectbox(
        "Assessment path",
        options=list(_SCENARIO_GROUPS),
        index=0,
        help="Choose the assessment area you want to demonstrate.",
    )

    available_scenarios = [
        scenario_name
        for scenario_name in _SCENARIO_GROUPS[group_name]
        if scenario_name in DEMO_SCENARIOS
    ]
    scenario_name = st.selectbox("Scenario", options=available_scenarios, index=0)
    scenario = DEMO_SCENARIOS[scenario_name]

    st.caption(scenario["description"])
    st.caption(
        f"Demonstration path: **{group_name.split(' · ', maxsplit=1)[-1]}** · "
        "the deterministic Rule Engine remains the source of truth."
    )

    try:
        position = build_demo_position(scenario_name)
    except Exception as error:
        st.error("Unable to construct the selected demo scenario.")
        st.exception(error)
        st.stop()

    with st.expander("Review input data", expanded=False):
        display_position_table(position)

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
