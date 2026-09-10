"""Financial analysis presentation for the credit assessment case."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.results.helpers import rule_indicator, rule_status


def build_indicator_analysis_frame(section: Any) -> pd.DataFrame:
    """Build analyst-facing indicator evidence without recalculating rule outcomes."""
    rows = []
    for rule in section.evidence:
        value = getattr(rule, "value", None)
        threshold = getattr(rule, "threshold", None)
        if value is None or threshold is None:
            continue

        rows.append(
            {
                "Rule": getattr(rule, "rule_id", ""),
                "Indicator": rule_indicator(rule),
                "Value": float(value),
                "Threshold": float(threshold),
                "Status": rule_status(rule),
            }
        )
    return pd.DataFrame(rows)


def _findings_by_rule(section: Any) -> dict[str, Any]:
    """Map deterministic findings to their originating rule."""
    findings = {}
    for finding in getattr(section, "findings", []) or []:
        result = getattr(finding, "result", None)
        rule_id = getattr(result, "rule_id", "")
        if rule_id:
            findings[rule_id] = finding
    return findings


def _finding_text(finding: Any) -> str:
    """Return the deterministic finding text for display."""
    if finding is None:
        return ""
    result = getattr(finding, "result", None)
    return str(
        getattr(result, "reason", None)
        or getattr(finding, "comment", None)
        or getattr(finding, "text", "")
    ).strip()


def _render_financial_dimensions(section: Any) -> None:
    """Show financial dimensions and their underlying deterministic evidence."""
    dimensions = getattr(section, "dimensions", {}) or {}
    if not dimensions:
        return

    findings_by_rule = _findings_by_rule(section)

    st.markdown("**Analytical Dimensions**")
    st.caption(
        "Each dimension links the indicator to its configured threshold, rule status and deterministic finding. "
        "This view does not introduce a new risk score or alter the assessment decision."
    )

    summary_rows = []
    for dimension, rules in dimensions.items():
        rule_list = list(rules or [])
        statuses = [rule_status(rule) for rule in rule_list]
        triggered = sum(status == "TRIGGERED" for status in statuses)
        evaluable = sum(status != "NOT_EVALUABLE" for status in statuses)
        if "TRIGGERED" in statuses:
            dimension_status = "TRIGGERED"
        elif evaluable:
            dimension_status = "NOT_TRIGGERED"
        else:
            dimension_status = "NOT_EVALUABLE"

        summary_rows.append(
            {
                "Analytical dimension": dimension,
                "Indicators": len(rule_list),
                "Triggered": triggered,
                "Status": dimension_status,
            }
        )

    summary_frame = pd.DataFrame(summary_rows)
    if summary_frame.empty:
        return

    st.dataframe(summary_frame, use_container_width=True, hide_index=True)

    for dimension, rules in dimensions.items():
        rule_list = list(rules or [])
        if not rule_list:
            continue

        st.markdown(f"**{dimension}**")
        detail_rows = []
        for rule in rule_list:
            rule_id = getattr(rule, "rule_id", "")
            detail_rows.append(
                {
                    "Rule": rule_id,
                    "Indicator": rule_indicator(rule),
                    "Value": getattr(rule, "value", None),
                    "Threshold": getattr(rule, "threshold", None),
                    "Status": rule_status(rule),
                    "Finding": _finding_text(findings_by_rule.get(rule_id)),
                }
            )
        st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)


def render_financial_analysis(section: Any) -> None:
    """Render financial dimensions and deterministic indicator evidence."""
    _render_financial_dimensions(section)


def render_behavioural_analysis(section: Any) -> None:
    """Render behavioural indicators against their configured thresholds."""
    frame = build_indicator_analysis_frame(section)
    if not frame.empty:
        st.markdown("**Indicator evidence**")
        st.dataframe(frame, use_container_width=True, hide_index=True)


def render_debt_analysis(section: Any) -> None:
    """Render debt-service indicators against their configured thresholds."""
    frame = build_indicator_analysis_frame(section)
    if not frame.empty:
        st.markdown("**Indicator evidence**")
        st.dataframe(frame, use_container_width=True, hide_index=True)
