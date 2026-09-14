from typing import Any

import pandas as pd
import streamlit as st

from app.demo_scenarios import DEMO_SCENARIOS, build_demo_case_data, build_demo_position
from app.ui.input import display_position_table
from src.models.position import CreditPosition

_DEMO_SCENARIO = "01 · Complete Credit Assessment"


def render_credit_data_source() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    """Render the synthetic demo case used by the application."""
    return _render_demo_scenario()


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

    st.subheader("Credit Position")
    st.markdown("**Complete Credit Assessment**")
    st.caption(scenario["description"])
    st.info(
        "This single demo case contains data for all four assessment domains. "
        "Review the synthetic inputs below before running the assessment."
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
