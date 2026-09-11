"""Compact cross-area risk driver presentation for the credit assessment case."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.results.helpers import rule_severity, rule_status, severity_rank


def build_risk_driver_frame(credit_case: Any) -> pd.DataFrame:
    """Build a compact view of triggered RuleResult data across macro-areas."""
    rows = []
    for section in getattr(credit_case, "sections", []) or []:
        for rule in getattr(section, "evidence", []) or []:
            if rule_status(rule).upper() != "TRIGGERED":
                continue

            rows.append(
                {
                    "Macro-area": getattr(section, "name", "Unknown"),
                    "Rule": getattr(rule, "rule_id", ""),
                    "Indicator": getattr(
                        rule, "indicator", getattr(rule, "rule_name", "Indicator")
                    ),
                    "Actual": getattr(rule, "value", None),
                    "Threshold": getattr(rule, "threshold", None),
                    "Severity": rule_severity(rule).upper(),
                }
            )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    frame["_severity_rank"] = frame["Severity"].map(severity_rank)
    return (
        frame.sort_values(
            ["_severity_rank", "Macro-area", "Rule"],
            ascending=[False, True, True],
            kind="stable",
        )
        .drop(columns="_severity_rank")
        .reset_index(drop=True)
    )


def render_risk_driver_overview(credit_case: Any) -> None:
    """Render triggered deterministic risk signals without introducing a new score."""
    frame = build_risk_driver_frame(credit_case)
    if frame.empty:
        return

    st.markdown("### Risk Drivers")
    st.caption("Triggered indicators grouped by macro-area and existing rule severity.")

    with st.expander("View triggered indicators", expanded=False):
        st.dataframe(frame, use_container_width=True, hide_index=True)
