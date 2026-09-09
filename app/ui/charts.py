from typing import Any

import pandas as pd
import streamlit as st

# ============================================================
# Shared Rule Result Helpers
# ============================================================


def _get_rule_results(result: Any) -> list[Any]:
    assessment = getattr(result, "assessment", None)
    return list(getattr(assessment, "rule_results", []) or [])


def _rule_status_counts(result: Any) -> dict[str, int]:
    """Count actual RuleResult statuses without applying business logic."""
    counts = {
        "TRIGGERED": 0,
        "NOT_TRIGGERED": 0,
        "NOT_EVALUABLE": 0,
    }

    for rule_result in _get_rule_results(result):
        status = getattr(getattr(rule_result, "status", None), "value", "")
        if status in counts:
            counts[status] += 1

    return counts


def _rule_status(rule_result: Any) -> str:
    status_obj = getattr(rule_result, "status", None)
    return str(getattr(status_obj, "value", str(status_obj or "—")))


def _rule_severity(rule_result: Any) -> str:
    severity_obj = getattr(rule_result, "severity", None)
    return str(getattr(severity_obj, "value", str(severity_obj or "—")))


# ============================================================
# Decision Path
# ============================================================


def render_decision_path(result: Any) -> None:
    """Explain visually how deterministic rule outcomes lead to the assessment."""
    rule_results = _get_rule_results(result)
    if not rule_results:
        return

    assessment = getattr(result, "assessment", None)
    status_obj = getattr(assessment, "status", None)
    assessment_status = str(getattr(status_obj, "value", str(status_obj or "Unknown")))

    counts = _rule_status_counts(result)
    triggered = counts["TRIGGERED"]

    st.subheader("How the Decision Is Produced")
    st.caption(
        "The assessment follows a traceable path from financial data to indicators, "
        "rule outcomes and final credit assessment."
    )

    steps = [
        ("01", "Financial Data", "Credit position"),
        ("02", "Indicators", f"{len(rule_results)} rules evaluated"),
        ("03", "Rule Outcomes", f"{triggered} triggered"),
        ("04", "Risk Drivers", "Severity & category"),
        ("05", "Assessment", assessment_status),
    ]

    cols = st.columns(len(steps))
    for index, (column, (number, title, description)) in enumerate(zip(cols, steps)):
        with column:
            with st.container(border=True):
                st.caption(number)
                st.markdown(f"**{title}**")
                st.caption(description)
        if index < len(steps) - 1:
            pass

    st.caption(
        "Decision principle: actual financial indicators are compared with configured "
        "thresholds; triggered rules become evidence for the final assessment."
    )


# ============================================================
# Risk Indicator Dashboard
# ============================================================


def render_risk_indicator_dashboard(result: Any) -> None:
    """Render a compact dashboard of rule indicators and risk categories."""
    rule_results = _get_rule_results(result)
    if not rule_results:
        return

    st.subheader("Risk Indicator Dashboard")
    st.caption(
        "Quantitative evidence behind the assessment: actual values, thresholds, "
        "rule outcomes and risk categories produced by the Rule Engine."
    )

    rows: list[dict[str, Any]] = []
    for rule_result in rule_results:
        rows.append(
            {
                "Rule": str(getattr(rule_result, "rule_id", "—")),
                "Indicator": str(getattr(rule_result, "rule_name", "—")),
                "Actual": getattr(rule_result, "value", None),
                "Threshold": getattr(rule_result, "threshold", None),
                "Status": _rule_status(rule_result),
                "Severity": _rule_severity(rule_result),
                "Category": str(getattr(rule_result, "category", "—")),
            }
        )

    dataframe = pd.DataFrame(rows)
    status_counts = _rule_status_counts(result)

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Rules evaluated", len(rule_results))
    with metric_cols[1]:
        st.metric("Triggered", status_counts["TRIGGERED"])
    with metric_cols[2]:
        st.metric("Not triggered", status_counts["NOT_TRIGGERED"])
    with metric_cols[3]:
        st.metric("Not evaluable", status_counts["NOT_EVALUABLE"])

    st.dataframe(
        dataframe[
            [
                "Rule",
                "Indicator",
                "Actual",
                "Threshold",
                "Status",
                "Severity",
                "Category",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    triggered = dataframe[dataframe["Status"] == "TRIGGERED"]
    if triggered.empty:
        st.success("No risk indicators breached their configured thresholds.")
        return

    st.markdown("#### Triggered Risk Drivers by Category")
    category_counts = (
        triggered.groupby("Category", dropna=False)
        .size()
        .reset_index(name="Triggered rules")
        .sort_values("Triggered rules", ascending=True)
    )

    st.bar_chart(
        category_counts,
        x="Category",
        y="Triggered rules",
        horizontal=True,
        height=max(180, 55 * len(category_counts)),
    )


# ============================================================
# Rule Assessment Summary
# ============================================================


def render_rule_assessment_summary(result: Any) -> None:
    """Render a visual summary of the deterministic rule engine."""
    rule_results = _get_rule_results(result)

    if not rule_results:
        return

    status_counts = _rule_status_counts(result)
    total_rules = sum(status_counts.values())

    labels = {
        "TRIGGERED": "Triggered",
        "NOT_TRIGGERED": "Not triggered",
        "NOT_EVALUABLE": "Not evaluable",
    }

    st.subheader("Assessment Evidence")
    st.caption(
        f"The Rule Engine evaluated {total_rules} rules. "
        "The distribution below shows the factual rule outcomes behind the assessment."
    )

    metric_cols = st.columns(3)

    metric_definitions = [
        ("Triggered", "TRIGGERED"),
        ("Not triggered", "NOT_TRIGGERED"),
        ("Not evaluable", "NOT_EVALUABLE"),
    ]

    for column, (label, status) in zip(metric_cols, metric_definitions):
        with column:
            st.metric(label, status_counts[status])

    chart_data = {
        "Status": [labels[status] for status in status_counts],
        "Rules": list(status_counts.values()),
    }

    st.bar_chart(
        chart_data,
        x="Status",
        y="Rules",
        horizontal=True,
        height=220,
    )

    render_rule_indicator_detail(result)


# ============================================================
# Rule Indicator Detail
# ============================================================


def render_rule_indicator_detail(result: Any) -> None:
    """Render the quantitative detail behind an individual rule result."""
    rule_results = _get_rule_results(result)

    if not rule_results:
        return

    st.markdown("#### Rule → Indicator → Value → Threshold")
    st.caption(
        "Select a rule to inspect the quantitative indicator, configured threshold "
        "and rationale used by the deterministic Rule Engine."
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
        if _rule_status(rule_result) == "TRIGGERED"
    ]

    default_index = triggered_indices[0] if triggered_indices else 0

    selected_label = st.selectbox(
        "Rule",
        rule_labels,
        index=default_index,
        key="rule_indicator_detail",
    )

    selected_index = rule_labels.index(selected_label)
    selected_rule = rule_results[selected_index]

    rule_id = getattr(selected_rule, "rule_id", "—")
    rule_name = getattr(selected_rule, "rule_name", "—")
    category = getattr(selected_rule, "category", "—")
    status = _rule_status(selected_rule)
    severity = _rule_severity(selected_rule)
    value = getattr(selected_rule, "value", None)
    threshold = getattr(selected_rule, "threshold", None)
    reason = getattr(selected_rule, "reason", None)

    info_cols = st.columns(4)

    with info_cols[0]:
        st.metric("Rule", str(rule_id))

    with info_cols[1]:
        st.metric("Status", status)

    with info_cols[2]:
        st.metric("Severity", severity)

    with info_cols[3]:
        st.metric("Category", str(category))

    st.markdown(f"**Indicator:** {rule_name}")

    if value is None or threshold is None:
        st.info(
            "The quantitative comparison cannot be displayed because "
            "the rule result does not contain both a value and a threshold."
        )
    else:
        value_float = float(value)
        threshold_float = float(threshold)

        comparison_data = {
            "Metric": ["Actual value", "Threshold"],
            "Value": [value_float, threshold_float],
        }

        st.bar_chart(
            comparison_data,
            x="Metric",
            y="Value",
            horizontal=True,
            height=180,
        )

        value_cols = st.columns(2)

        with value_cols[0]:
            st.metric("Actual value", f"{value_float:g}")

        with value_cols[1]:
            st.metric("Threshold", f"{threshold_float:g}")

    if reason:
        st.markdown("**Why did this rule produce this result?**")
        st.info(reason)
