from typing import Any

import streamlit as st

# ============================================================
# Rule Assessment Summary
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


def render_rule_assessment_summary(result: Any) -> None:
    """
    Render a visual summary of the deterministic rule engine.

    The component uses only the RuleResult objects produced by the
    assessment engine. No assessment or threshold logic is recalculated.
    """
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
    """
    Render the quantitative detail behind an individual rule result.

    The component exposes the actual value and configured threshold
    already produced by the deterministic rule engine. It does not
    recalculate or alter any assessment logic.
    """
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
        if getattr(getattr(rule_result, "status", None), "value", "") == "TRIGGERED"
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

    status_obj = getattr(selected_rule, "status", None)
    status = getattr(status_obj, "value", str(status_obj or "—"))

    severity_obj = getattr(selected_rule, "severity", None)
    severity = getattr(severity_obj, "value", str(severity_obj or "—"))

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
