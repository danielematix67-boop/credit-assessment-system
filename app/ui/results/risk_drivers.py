"""Cross-area risk driver presentation for the credit assessment case."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.results.helpers import rule_status


def build_risk_driver_frame(credit_case: Any) -> pd.DataFrame:
    """Build a cross-area view of deterministic triggered RuleResult evidence."""
    rows = []
    for section in getattr(credit_case, "sections", []) or []:
        for rule in getattr(section, "evidence", []) or []:
            if rule_status(rule).upper() != "TRIGGERED":
                continue

            value = getattr(rule, "value", None)
            threshold = getattr(rule, "threshold", None)
            if value is not None:
                value = float(value)
            if threshold is not None:
                threshold = float(threshold)

            rows.append(
                {
                    "Macro-area": getattr(section, "name", "Unknown"),
                    "Rule": getattr(rule, "rule_id", ""),
                    "Indicator": getattr(
                        rule, "indicator", getattr(rule, "rule_name", "Indicator")
                    ),
                    "Value": value,
                    "Threshold": threshold,
                    "Status": "TRIGGERED",
                    "Severity": str(
                        getattr(
                            getattr(rule, "severity", None),
                            "value",
                            getattr(rule, "severity", ""),
                        )
                    ).upper(),
                }
            )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    return frame.sort_values(
        ["Macro-area", "Rule"], ascending=True, kind="stable"
    ).reset_index(drop=True)


def render_risk_driver_overview(credit_case: Any) -> None:
    """Render deterministic indicators that actually generated risk findings."""
    frame = build_risk_driver_frame(credit_case)
    if frame.empty:
        return

    st.markdown("### Risk Driver Overview")
    st.caption(
        "Indicators shown here are deterministic rules that triggered a risk finding. "
        "The view reports the observed value, configured threshold and severity without introducing an additional score."
    )

    st.dataframe(frame, use_container_width=True, hide_index=True)
