from typing import Any

import streamlit as st


# ============================================================
# Rule Assessment Summary
# ============================================================


def render_rule_assessment_summary(
    result: Any,
) -> None:
    """
    Render a visual summary of the deterministic rule engine.

    The chart uses the actual RuleResult status values produced by
    the assessment engine. No additional business logic is applied
    in the presentation layer.
    """

    assessment = getattr(result, "assessment", None)

    if assessment is None:
        return

    rule_results = getattr(
        assessment,
        "rule_results",
        [],
    )

    if not rule_results:
        return

    status_counts = {
        "TRIGGERED": 0,
        "NOT_TRIGGERED": 0,
        "NOT_EVALUABLE": 0,
    }

    for rule_result in rule_results:
        status = getattr(
            getattr(rule_result, "status", None),
            "value",
            str(getattr(rule_result, "status", "")),
        )

        if status in status_counts:
            status_counts[status] += 1

    labels = {
        "TRIGGERED": "Triggered",
        "NOT_TRIGGERED": "Not triggered",
        "NOT_EVALUABLE": "Not evaluable",
    }

    chart_data = {
        "Status": [
            labels[status]
            for status in status_counts
        ],
        "Rules": list(status_counts.values()),
    }

    st.subheader("Rule Assessment Summary")

    st.caption(
        "Distribution of the rules evaluated by the deterministic "
        "Rule Engine."
    )

    metric_cols = st.columns(3)

    metric_definitions = [
        ("Triggered", "TRIGGERED"),
        ("Not triggered", "NOT_TRIGGERED"),
        ("Not evaluable", "NOT_EVALUABLE"),
    ]

    for column, (label, status) in zip(
        metric_cols,
        metric_definitions,
    ):
        with column:
            st.metric(
                label,
                status_counts[status],
            )

    st.bar_chart(
        chart_data,
        x="Status",
        y="Rules",
        horizontal=True,
        height=220,
    )


# ============================================================
# Rule Indicator Detail
# ============================================================


def render_rule_indicator_detail(
    result: Any,
) -> None:
    """
    Render the quantitative detail behind an individual rule result.

    The component exposes the actual value and configured threshold
    already produced by the deterministic rule engine. It does not
    recalculate or alter any assessment logic.
    """

    assessment = getattr(result, "assessment", None)

    if assessment is None:
        return

    rule_results = list(
        getattr(assessment, "rule_results", []) or []
    )

    if not rule_results:
        return

    st.subheader("Rule → Indicator → Value → Threshold")
    st.caption(
        "Select a rule to see the quantitative indicator used by the "
        "deterministic Rule Engine, together with its configured threshold."
    )

    rule_labels = []
    for rule_result in rule_results:
        rule_id = str(getattr(rule_result, "rule_id", ""))
        rule_name = str(getattr(rule_result, "rule_name", ""))
        label = f"{rule_id} — {rule_name}" if rule_name else rule_id
        rule_labels.append(label)

    selected_label = st.selectbox(
        "Rule",
        rule_labels,
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
    severity = getattr(
        severity_obj,
        "value",
        str(severity_obj or "—"),
    )

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
        st.markdown("**Why?**")
        st.info(reason)
