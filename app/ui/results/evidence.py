"""Rule evidence matrix visualization for the Results page."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.results.helpers import (
    format_indicator_value,
    get_rule_results,
    rule_indicator,
    rule_severity,
    rule_status,
    status_label,
)


def render_rule_evidence_matrix(result: Any) -> None:
    """Show a compact, display-only matrix of deterministic rule evidence."""
    rule_results = get_rule_results(result)
    if not rule_results:
        return

    st.markdown("#### Rule Evidence Matrix")
    st.caption(
        "The matrix shows how each deterministic indicator is evaluated against its "
        "configured threshold and records the resulting rule outcome."
    )

    rows: list[dict[str, Any]] = []
    for rule_result in rule_results:
        rows.append(
            {
                "Rule": str(getattr(rule_result, "rule_id", "—")),
                "Indicator": rule_indicator(rule_result),
                "Actual": format_indicator_value(getattr(rule_result, "value", None)),
                "Threshold": format_indicator_value(
                    getattr(rule_result, "threshold", None)
                ),
                "Status": status_label(rule_status(rule_result)),
                "Severity": rule_severity(rule_result),
            }
        )

    matrix = pd.DataFrame(rows)
    st.dataframe(
        matrix,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rule": st.column_config.TextColumn("Rule", width="small"),
            "Indicator": st.column_config.TextColumn("Indicator", width="medium"),
            "Actual": st.column_config.TextColumn("Actual", width="small"),
            "Threshold": st.column_config.TextColumn("Threshold", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Severity": st.column_config.TextColumn("Severity", width="small"),
        },
    )
    st.caption(
        "Presentation-only evidence view. Values, thresholds, status and severity are "
        "read directly from RuleResult and are not recalculated by the UI."
    )
