from typing import Any

import streamlit as st

from app.demo_scenarios import (
    DEMO_SCENARIOS,
    build_demo_position,
)
from app.ui.credit_position import (
    build_credit_position_from_ui,
    build_scenario_data_table,
)
from src.models.position import CreditPosition

# ============================================================
# Credit Data Source
# ============================================================


def render_credit_data_source() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    """
    Render the credit-data input section.

    Supports two input modes:

    - Demo Scenario
    - Manual Input

    Returns
    -------
    tuple
        position:
            CreditPosition created from the selected input.

        position_data:
            Raw manual-input data, if Manual Input is selected.

        input_mode:
            Selected input mode.

        scenario_name:
            Selected demo scenario, or None for manual input.
    """

    # ========================================================
    # Section Header
    # ========================================================

    st.subheader("Credit Data")

    st.caption(
        "Select a predefined scenario for the demonstration "
        "or switch to manual input for custom testing."
    )

    # ========================================================
    # Input Mode
    # ========================================================

    input_mode = st.radio(
        "Input Mode",
        options=[
            "Demo Scenario",
            "Manual Input",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

    # ========================================================
    # Demo Scenario
    # ========================================================

    if input_mode == "Demo Scenario":
        return _render_demo_scenario()

    # ========================================================
    # Manual Input
    # ========================================================

    return _render_manual_input()


# ============================================================
# Demo Scenario
# ============================================================


def _render_demo_scenario() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    """
    Render the predefined demo-scenario input.
    """

    scenario_name = st.selectbox(
        "Demo Scenario",
        options=list(DEMO_SCENARIOS.keys()),
        index=0,
    )

    scenario = DEMO_SCENARIOS[scenario_name]

    # --------------------------------------------------------
    # Scenario Card
    # --------------------------------------------------------

    _render_scenario_card(
        scenario_name=scenario_name,
        description=scenario["description"],
    )

    # --------------------------------------------------------
    # Build Demo Position
    # --------------------------------------------------------

    try:
        position = build_demo_position(scenario_name)

    except Exception as error:
        st.error("Unable to construct the selected demo scenario.")

        st.exception(error)

        st.stop()

    # --------------------------------------------------------
    # Scenario Data
    # --------------------------------------------------------

    st.markdown("#### Scenario Data")

    st.markdown(
        """
        <div class="data-introduction">
            The following values represent the financial data
            provided as input to the credit assessment system.
            They are <strong>not assessment results</strong>.
            The deterministic rule engine evaluates these inputs
            against the configured rules and thresholds during
            the assessment workflow.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="data-note">
            <strong>Input data vs. assessment result</strong><br>
            Financial indicators supplied to the system are
            displayed separately from rule findings, severity
            and assessment status. These assessment outputs
            are calculated by the deterministic decision layer.
        </div>
        """,
        unsafe_allow_html=True,
    )

    scenario_data = build_scenario_data_table(position)

    st.dataframe(
        scenario_data,
        width="stretch",
        hide_index=True,
        column_config={
            "Financial Indicator": (
                st.column_config.TextColumn(
                    "Financial Indicator",
                    width="medium",
                )
            ),
            "Value": (
                st.column_config.TextColumn(
                    "Value",
                    width="medium",
                )
            ),
            "Unit": (
                st.column_config.TextColumn(
                    "Unit",
                    width="small",
                )
            ),
            "Description": (
                st.column_config.TextColumn(
                    "What it represents",
                    width="large",
                )
            ),
        },
    )

    return (
        position,
        None,
        "Demo Scenario",
        scenario_name,
    )


# ============================================================
# Manual Input
# ============================================================


def _render_manual_input() -> tuple[
    CreditPosition | None,
    dict[str, Any] | None,
    str,
    str | None,
]:
    """
    Render the manual credit-position input form.
    """

    st.info(
        "Manual mode is intended for custom testing. "
        "For demonstrations, use Demo Scenario mode."
    )

    position_data = build_credit_position_from_ui()

    provided_fields = sum(value is not None for value in position_data.values())

    missing_fields = len(position_data) - provided_fields

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.metric(
            "Model Fields",
            len(position_data),
        )

    with summary_col2:
        st.metric(
            "Provided",
            provided_fields,
        )

    with summary_col3:
        st.metric(
            "Missing",
            missing_fields,
        )

    return (
        None,
        position_data,
        "Manual Input",
        None,
    )


# ============================================================
# Scenario Card
# ============================================================


def _render_scenario_card(
    *,
    scenario_name: str,
    description: str,
) -> None:
    """
    Render the visual card for a demo scenario.
    """

    st.html(
        f"""
        <div class="scenario-card">
            <div class="scenario-title">
                {scenario_name}
            </div>
            <div class="scenario-description">
                {description}
            </div>
        </div>
        """
    )
