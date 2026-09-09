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
