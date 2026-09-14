from dataclasses import fields
from typing import Any

import pandas as pd
import streamlit as st

from app.demo_scenarios import DEMO_SCENARIOS, build_demo_case_data, build_demo_position
from app.ui.input import (
    build_credit_position_from_ui,
    build_manual_case_data_from_ui,
    display_position_table,
)
from src.models.behavioural_data import BehaviouralData
from src.models.customer_profile_data import CustomerProfileData
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.position import CreditPosition

_DEMO_SCENARIO = "01 · Complete Credit Assessment"


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
    """Render the single complete synthetic case with a user-friendly data preview."""
    for key in (
        "manual_customer_profile_data",
        "manual_behavioural_data",
        "manual_debt_sustainability_data",
    ):
        st.session_state.pop(key, None)

    scenario_name = _DEMO_SCENARIO
    scenario = DEMO_SCENARIOS[scenario_name]

    st.markdown("**Complete Credit Assessment**")
    st.caption(scenario["description"])
    st.info(
        "This single demo case contains data for all four assessment domains. "
        "Use the preview below to understand the inputs before running the assessment."
    )

    try:
        position = build_demo_position(scenario_name)
        customer_profile, behavioural, debt_sustainability = build_demo_case_data(
            scenario_name
        )
    except Exception as error:
        st.error("Unable to construct the demo scenario.")
        st.exception(error)
        st.stop()

    domain_columns = st.columns(4)
    domain_labels = (
        "Customer Profile",
        "Financial Analysis",
        "Behavioural Analysis",
        "Debt Sustainability",
    )
    for column, label in zip(domain_columns, domain_labels):
        with column:
            st.metric(label, "Available")

    with st.expander("Review complete input data", expanded=False):
        tab_profile, tab_financial, tab_behavioural, tab_debt = st.tabs(
            [
                "Customer Profile",
                "Financial Analysis",
                "Behavioural Analysis",
                "Debt Sustainability",
            ]
        )

        with tab_profile:
            _render_object_table(customer_profile)
        with tab_financial:
            display_position_table(position)
        with tab_behavioural:
            _render_object_table(behavioural)
        with tab_debt:
            _render_object_table(debt_sustainability)

    st.caption(
        "The values above are synthetic demonstration data. The deterministic Rule Engine "
        "evaluates the complete case; the LLM layer does not alter rule outcomes."
    )

    return position, None, "Demo Scenario", scenario_name


def _render_object_table(data: Any) -> None:
    """Render a dataclass-like domain object as a compact key/value table."""
    if data is None:
        st.info("No data available for this assessment domain.")
        return

    if hasattr(data, "__dataclass_fields__"):
        rows = []
        for field_name in data.__dataclass_fields__:
            value = getattr(data, field_name, None)
            if isinstance(value, (list, tuple)):
                value = ", ".join(map(str, value))
            rows.append({"Field": field_name, "Value": value})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        return

    if isinstance(data, dict):
        st.dataframe(
            pd.DataFrame(
                [{"Field": key, "Value": value} for key, value in data.items()]
            ),
            use_container_width=True,
            hide_index=True,
        )
        return

    st.write(data)


def _count_input_fields(data_objects: tuple[Any, ...]) -> tuple[int, int]:
    """Return total and populated field counts across all input data models."""
    total = 0
    populated = 0

    for data in data_objects:
        for field in fields(data):
            total += 1
            value = getattr(data, field.name)
            if value is not None and value != []:
                populated += 1

    return total, populated


def _render_manual_input() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    """Render complete manual input for every model used by the assessment."""
    st.caption(
        "Enter all information available for the credit review. "
        "The form covers every field in the CreditPosition model and all "
        "additional domain data models used by the assessment workflow."
    )

    position_data = build_credit_position_from_ui()
    customer_profile, behavioural, debt_sustainability = build_manual_case_data_from_ui()

    st.session_state["manual_customer_profile_data"] = customer_profile
    st.session_state["manual_behavioural_data"] = behavioural
    st.session_state["manual_debt_sustainability_data"] = debt_sustainability

    position = CreditPosition(**position_data)
    total_fields, populated_fields = _count_input_fields(
        (position, customer_profile, behavioural, debt_sustainability)
    )

    columns = st.columns(3)
    with columns[0]:
        st.metric("Fields", total_fields)
    with columns[1]:
        st.metric("Available", populated_fields)
    with columns[2]:
        st.metric("Missing", total_fields - populated_fields)

    return position, position_data, "Manual Input", None
