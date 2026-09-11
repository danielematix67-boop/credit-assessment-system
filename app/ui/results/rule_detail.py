"""Single-rule indicator detail visualization."""

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


def render_rule_indicator_detail(result: Any) -> None:
    """Render a professional, display-only risk indicator card."""
    rule_results = get_rule_results(result)
    if not rule_results:
        return

    st.markdown("##### Risk Indicator Detail")
    st.caption(
        "Inspect the deterministic Rule Engine output for one indicator, including "
        "the observed value, configured threshold and resulting status."
    )

    rule_labels = []
    for rule_result in rule_results:
        rule_id = str(getattr(rule_result, "rule_id", ""))
        rule_name = str(getattr(rule_result, "rule_name", ""))
        label = f"{rule_id} — {rule_name}" if rule_name else rule_id
        rule_labels.append(label)

    triggered_indices = [
        index
        for index, rule_result in enumerate(rule_results)
        if rule_status(rule_result) == "TRIGGERED"
    ]
    default_index = triggered_indices[0] if triggered_indices else 0

    selected_label = st.selectbox(
        "Indicator",
        rule_labels,
        index=default_index,
        key="rule_indicator_detail",
    )
    selected_index = rule_labels.index(selected_label)
    selected_rule = rule_results[selected_index]

    rule_id = str(getattr(selected_rule, "rule_id", "—"))
    rule_name = str(getattr(selected_rule, "rule_name", "—"))
    indicator = rule_indicator(selected_rule)
    category = str(getattr(selected_rule, "category", "—"))
    status = rule_status(selected_rule)
    severity = rule_severity(selected_rule)
    value = getattr(selected_rule, "value", None)
    threshold = getattr(selected_rule, "threshold", None)
    reason = getattr(selected_rule, "reason", None)

    status_text = status_label(status)
    severity_text = severity.upper()

    # Presentation-only card. All displayed values come directly from RuleResult.
    with st.container(border=True):
        header_cols = st.columns([4.5, 1.5])
        with header_cols[0]:
            st.caption(f"{rule_id}  ·  {category}")
            st.markdown(f"### {indicator}")
            if rule_name and rule_name != indicator:
                st.caption(rule_name)
        with header_cols[1]:
            st.metric("Risk level", severity_text)

        value_cols = st.columns(2)
        with value_cols[0]:
            st.caption("Observed value")
            st.markdown(f"## {format_indicator_value(value)}")
        with value_cols[1]:
            st.caption("Configured threshold")
            st.markdown(f"## {format_indicator_value(threshold)}")

        if value is not None and threshold is not None:
            chart_data = pd.DataFrame(
                {
                    "Measure": ["Actual", "Threshold"],
                    "Value": [float(value), float(threshold)],
                }
            )
            st.bar_chart(chart_data, x="Measure", y="Value", height=170)

        meta_cols = st.columns(2)
        with meta_cols[0]:
            st.caption("Status")
            st.markdown(f"**{status_text}**")
        with meta_cols[1]:
            st.caption("Category")
            st.markdown(f"**{category}**")

        if reason:
            st.markdown("**Rationale**")
            st.write(reason)

    st.caption(
        "The card presents the Rule Engine output as-is; it does not recalculate "
        "thresholds, severity or assessment status."
    )
