from typing import Any

import pandas as pd
import streamlit as st

from app.ui.input import display_position_table
from src.models.position import CreditPosition
from src.services.excel_scenario_loader import ExcelScenarioError, load_excel_scenarios


def render_credit_data_source() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    """Render the Excel workbook as the sole application data source."""
    return _render_excel_upload()


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
    """Render and validate scenarios loaded from the uploaded Excel workbook."""
    for key in (
        "assessment_customer_profile_data",
        "assessment_behavioural_data",
        "assessment_debt_sustainability_data",
    ):
        st.session_state.pop(key, None)

    st.subheader("Credit Data Input")
    st.caption(
        "The Excel workbook is the single source of synthetic demonstration data. "
        "No built-in demo scenario is maintained in the application."
    )

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
