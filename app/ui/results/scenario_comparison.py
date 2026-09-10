"""Analyst-oriented comparison of synthetic demo scenarios."""

from typing import Any

import pandas as pd
import streamlit as st

from app.demo_scenarios import DEMO_SCENARIOS

INDICATORS: dict[str, str] = {
    "Revenue growth": "revenue_growth",
    "EBITDA margin": "ebitda_margin",
    "NFP / EBITDA": "nfp_to_ebitda",
    "Interest expense": "interest_expense",
}


def build_scenario_comparison_frame() -> pd.DataFrame:
    """Build a descriptive comparison from synthetic scenario inputs only."""
    rows: list[dict[str, Any]] = []
    for scenario_name, scenario in DEMO_SCENARIOS.items():
        values = scenario["values"]
        rows.append(
            {
                "Scenario": scenario_name,
                "Revenue growth": values.get("revenue_growth"),
                "EBITDA margin": values.get("ebitda_margin"),
                "NFP / EBITDA": values.get("nfp_to_ebitda"),
                "Interest expense": values.get("interest_expense"),
            }
        )
    return pd.DataFrame(rows)


def _format_indicator_frame(frame: pd.DataFrame, indicator: str) -> pd.DataFrame:
    """Prepare the selected indicator for a readable Streamlit table."""
    display = frame[["Scenario", indicator]].copy()
    display[indicator] = display[indicator].map(
        lambda value: "—" if pd.isna(value) else f"{value:,.2f}"
    )
    return display


def render_scenario_comparison(current_scenario: str | None) -> None:
    """Render a factual benchmark across the available synthetic demo scenarios."""
    if not current_scenario or current_scenario not in DEMO_SCENARIOS:
        return

    frame = build_scenario_comparison_frame()

    st.markdown("### Scenario Comparison")
    st.caption(
        "Compare the synthetic demo cases on selected credit-risk indicators. "
        "This benchmark is descriptive: it does not recalculate or override the Rule Engine assessment."
    )

    indicator = st.selectbox(
        "Indicator",
        list(INDICATORS),
        key="scenario_comparison_indicator",
    )

    chart_frame = frame.set_index("Scenario")[[indicator]].copy()
    if indicator in {"Revenue growth", "EBITDA margin"}:
        chart_frame[indicator] = chart_frame[indicator] * 100

    st.bar_chart(chart_frame, horizontal=True)

    current_row = frame.loc[frame["Scenario"] == current_scenario]
    if not current_row.empty:
        current_value = current_row.iloc[0][indicator]
        if pd.isna(current_value):
            st.info(f"Current scenario: **{current_scenario}** — indicator not available.")
        else:
            suffix = "%" if indicator in {"Revenue growth", "EBITDA margin"} else ""
            shown_value = float(current_value) * 100 if suffix else float(current_value)
            st.info(
                f"Current scenario: **{current_scenario}** · "
                f"{indicator}: **{shown_value:,.2f}{suffix}**"
            )

    with st.expander("View comparison data", expanded=False):
        st.dataframe(
            _format_indicator_frame(frame, indicator),
            use_container_width=True,
            hide_index=True,
        )
