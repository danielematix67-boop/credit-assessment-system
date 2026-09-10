"""Compact cross-area risk driver presentation for the credit assessment case."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.results.helpers import rule_direction, rule_status, threshold_distance, threshold_relation


def build_risk_driver_frame(credit_case: Any) -> pd.DataFrame:
    """Build a cross-area ranking from deterministic triggered RuleResult data."""
    rows = []
    for section in getattr(credit_case, "sections", []) or []:
        for rule in getattr(section, "evidence", []) or []:
            if rule_status(rule).upper() != "TRIGGERED":
                continue

            value = getattr(rule, "value", None)
            threshold = getattr(rule, "threshold", None)
            distance = None
            relation = "Not evaluable"
            if value is not None and threshold is not None:
                value = float(value)
                threshold = float(threshold)
                distance = threshold_distance(
                    value, threshold, rule_direction(rule).upper()
                )
                relation = threshold_relation(distance)

            rows.append(
                {
                    "Macro-area": getattr(section, "name", "Unknown"),
                    "Rule": getattr(rule, "rule_id", ""),
                    "Indicator": getattr(
                        rule, "indicator", getattr(rule, "rule_name", "Indicator")
                    ),
                    "Value": value,
                    "Threshold": threshold,
                    "Severity": str(
                        getattr(
                            getattr(rule, "severity", None),
                            "value",
                            getattr(rule, "severity", ""),
                        )
                    ).upper(),
                    "Distance": distance,
                    "Relation": relation,
                }
            )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    return frame.sort_values(
        "Distance", ascending=False, na_position="last", kind="stable"
    ).reset_index(drop=True)


def render_risk_driver_overview(credit_case: Any) -> None:
    """Render the highest-priority deterministic risk drivers across macro-areas."""
    frame = build_risk_driver_frame(credit_case)
    if frame.empty:
        return

    st.markdown("### Risk Drivers")

    chart_frame = frame.dropna(subset=["Distance"]).head(10)
    if not chart_frame.empty:
        chart_frame = chart_frame.set_index("Indicator")[["Distance"]].rename(
            columns={"Distance": "Threshold distance"}
        )
        st.bar_chart(chart_frame, horizontal=True, height=240)

    display_frame = frame.copy()
    display_frame["Distance"] = display_frame["Distance"].map(
        lambda value: "—" if pd.isna(value) else f"{value:+.0%}"
    )
    with st.expander("View triggered indicators", expanded=False):
        st.dataframe(display_frame, use_container_width=True, hide_index=True)
