from typing import Any

import pandas as pd
import streamlit as st

from app.demo_scenarios import DEMO_SCENARIOS, build_demo_case_data, build_demo_position
from app.ui.input import display_position_table
from src.models.position import CreditPosition
from src.services.excel_scenario_loader import ExcelScenarioError, load_excel_scenarios

_DEMO_SCENARIO = "01 · Complete Credit Assessment"


def render_credit_data_source() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    """Render the selected credit-data source used by the application."""
    source = st.radio(
        "Data Source",
        ["Demo Scenario", "Excel Upload"],
        horizontal=True,
        key="credit_data_source",
    )

    if source == "Excel Upload":
        return _render_excel_upload()

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


def _render_excel_upload() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    """Render and validate scenarios loaded from an uploaded Excel workbook."""
    for key in (
        "assessment_customer_profile_data",
        "assessment_behavioural_data",
        "assessment_debt_sustainability_data",
    ):
        st.session_state.pop(key, None)

    uploaded_file = st.file_uploader(
        "Upload Excel scenario workbook",
        type=["xlsx"],
        help=(
            "The workbook must contain a Credit_Position sheet. Customer_Profile, "
            "Behavioural and Debt_Sustainability are optional."
        ),
    )
    if uploaded_file is None:
        st.info("Upload an .xlsx workbook to load assessment scenarios.")
        return None, None, "Excel Upload", None

    try:
        scenarios = load_excel_scenarios(uploaded_file)
    except ExcelScenarioError as error:
        st.error(str(error))
        return None, None, "Excel Upload", None

    scenario_names = list(scenarios)
    selected = st.selectbox("Scenario", scenario_names)
    position, customer_profile, behavioural, debt_sustainability = scenarios[selected]

    st.success(f"Loaded {len(scenario_names)} scenario(s). Selected: **{selected}**")
    st.subheader("Credit Position")
    st.caption("Data loaded from the uploaded workbook and mapped to the native domain models.")

    domain_columns = st.columns(4)
    domain_values = (
        ("Customer Profile", customer_profile),
        ("Financial Analysis", position),
        ("Behavioural Analysis", behavioural),
        ("Debt Sustainability", debt_sustainability),
    )
    for column, (label, value) in zip(domain_columns, domain_values):
        with column:
            st.metric(label, "Available" if value is not None else "Not provided")

    with st.expander("Review uploaded input data", expanded=False):
        tab_profile, tab_financial, tab_behavioural, tab_debt = st.tabs(
            ["Customer Profile", "Financial Analysis", "Behavioural Analysis", "Debt Sustainability"]
        )
        with tab_profile:
            _render_object_table(customer_profile)
        with tab_financial:
            display_position_table(position)
        with tab_behavioural:
            _render_object_table(behavioural)
        with tab_debt:
            _render_object_table(debt_sustainability)

    st.session_state["assessment_customer_profile_data"] = customer_profile
    st.session_state["assessment_behavioural_data"] = behavioural
    st.session_state["assessment_debt_sustainability_data"] = debt_sustainability

    return position, None, "Excel Upload", selected
