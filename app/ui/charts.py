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
    counts = {"TRIGGERED": 0, "NOT_TRIGGERED": 0, "NOT_EVALUABLE": 0}
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


def _rule_direction(rule_result: Any) -> str:
    direction_obj = getattr(rule_result, "direction", None)
    return str(getattr(direction_obj, "value", str(direction_obj or "—")))


def _severity_rank(severity: str) -> int:
    """Return a display-only severity ranking."""
    return {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(
        severity.upper(), 0
    )


def _rule_indicator(rule_result: Any) -> str:
    """Return the explicit deterministic indicator, with legacy fallback."""
    return str(
        getattr(rule_result, "indicator", None)
        or getattr(rule_result, "rule_name", "—")
    )


def _severity_counts(rule_results: list[Any]) -> dict[str, int]:
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for rule_result in rule_results:
        severity = _rule_severity(rule_result).upper()
        if severity in counts:
            counts[severity] += 1
    return counts


def _format_indicator_value(value: Any) -> str:
    """Format an already-computed indicator for display only."""
    if value is None:
        return "—"
    try:
        return f"{float(value):g}"
    except (TypeError, ValueError):
        return str(value)


def _status_label(status: str) -> str:
    return {
        "TRIGGERED": "TRIGGERED",
        "NOT_TRIGGERED": "NOT TRIGGERED",
        "NOT_EVALUABLE": "NOT EVALUABLE",
    }.get(status, status.replace("_", " "))


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
    assessment_status = str(
        getattr(status_obj, "value", str(status_obj or "Unknown"))
    )
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
    for column, (number, title, description) in zip(cols, steps):
        with column:
            with st.container(border=True):
                st.caption(number)
                st.markdown(f"**{title}**")
                st.caption(description)

    st.caption(
        "Decision principle: actual financial indicators are compared with configured "
        "thresholds; triggered rules become evidence for the final assessment."
    )


# ============================================================
# Risk Indicator Dashboard
# ============================================================


def render_risk_indicator_dashboard(result: Any) -> None:
    """Render the complete rule-outcome and indicator diagnostic dashboard."""
    rule_results = _get_rule_results(result)
    if not rule_results:
        return

    st.subheader("Risk Indicator Dashboard")
    st.caption(
        "A structured view of the deterministic indicators, rule outcomes and risk severity."
    )

    rows: list[dict[str, Any]] = []
    for rule_result in rule_results:
        rows.append(
            {
                "Rule": str(getattr(rule_result, "rule_id", "—")),
                "Indicator": _rule_indicator(rule_result),
                "Actual": getattr(rule_result, "value", None),
                "Threshold": getattr(rule_result, "threshold", None),
                "Status": _rule_status(rule_result),
                "Severity": _rule_severity(rule_result),
                "Category": str(getattr(rule_result, "category", "—")),
            }
        )

    dataframe = pd.DataFrame(rows)
    status_counts = _rule_status_counts(result)
    severity_counts = _severity_counts(rule_results)

    metric_cols = st.columns(4)
    metrics = [
        ("Indicators", len(rule_results)),
        ("Triggered", status_counts["TRIGGERED"]),
        ("High / critical", severity_counts["HIGH"] + severity_counts["CRITICAL"]),
        ("Not evaluable", status_counts["NOT_EVALUABLE"]),
    ]
    for column, (label, value) in zip(metric_cols, metrics):
        with column:
            st.metric(label, value)

    st.markdown("#### Risk Signal Overview")
    overview_cols = st.columns(2)
    with overview_cols[0]:
        labels = {
            "TRIGGERED": "Triggered",
            "NOT_TRIGGERED": "Not triggered",
            "NOT_EVALUABLE": "Not evaluable",
        }
        status_data = pd.DataFrame(
            {
                "Status": [labels[key] for key in status_counts],
                "Rules": list(status_counts.values()),
            }
        )
        st.caption("Rule outcomes")
        st.bar_chart(status_data, x="Status", y="Rules", horizontal=True, height=190)

    with overview_cols[1]:
        severity_data = pd.DataFrame(
            {
                "Severity": list(severity_counts.keys()),
                "Rules": list(severity_counts.values()),
            }
        )
        st.caption("Severity profile")
        st.bar_chart(severity_data, x="Severity", y="Rules", horizontal=True, height=190)

    st.caption(
        "Both views describe the factual Rule Engine output; they do not recalculate the assessment."
    )

    st.markdown("#### Rule Catalogue")
    st.caption("Filter the complete rule set before inspecting individual rule evidence.")

    filter_cols = st.columns([1.2, 1.2, 1.6, 1.4])
    with filter_cols[0]:
        status_options = ["All", "TRIGGERED", "NOT_TRIGGERED", "NOT_EVALUABLE"]
        selected_status = st.selectbox(
            "Status",
            status_options,
            index=1 if status_counts["TRIGGERED"] else 0,
            key="rule_catalogue_status",
        )

    with filter_cols[1]:
        severity_values = sorted(
            {
                str(value)
                for value in dataframe["Severity"].dropna().tolist()
                if str(value) not in {"", "—"}
            },
            key=_severity_rank,
            reverse=True,
        )
        selected_severity = st.selectbox(
            "Severity",
            ["All", *severity_values],
            key="rule_catalogue_severity",
        )

    with filter_cols[2]:
        categories = sorted(
            {
                str(value)
                for value in dataframe["Category"].dropna().tolist()
                if str(value) not in {"", "—"}
            }
        )
        selected_category = st.selectbox(
            "Category",
            ["All", *categories],
            key="rule_catalogue_category",
        )

    with filter_cols[3]:
        selected_sort = st.selectbox(
            "Sort by",
            ["Priority", "Rule ID", "Category", "Status"],
            key="rule_catalogue_sort",
        )

    filtered = dataframe.copy()
    if selected_status != "All":
        filtered = filtered[filtered["Status"] == selected_status]
    if selected_severity != "All":
        filtered = filtered[filtered["Severity"] == selected_severity]
    if selected_category != "All":
        filtered = filtered[filtered["Category"] == selected_category]

    filtered["_priority"] = filtered.apply(
        lambda row: (
            0 if row["Status"] == "TRIGGERED" else 1,
            -_severity_rank(str(row["Severity"])),
            str(row["Rule"]),
        ),
        axis=1,
    )

    if selected_sort == "Priority":
        filtered = filtered.sort_values("_priority", ascending=True)
    elif selected_sort == "Rule ID":
        filtered = filtered.sort_values("Rule", ascending=True)
    elif selected_sort == "Category":
        filtered = filtered.sort_values(["Category", "Rule"], ascending=True)
    else:
        filtered = filtered.sort_values(["Status", "Rule"], ascending=True)

    total_filtered = len(filtered)
    st.caption(f"Showing {total_filtered} of {len(dataframe)} evaluated rules.")
    display_columns = [
        "Rule",
        "Indicator",
        "Actual",
        "Threshold",
        "Status",
        "Severity",
        "Category",
    ]

    with st.expander("View filtered rule results", expanded=total_filtered <= 20):
        if filtered.empty:
            st.info("No rules match the selected filters.")
        else:
            st.dataframe(
                filtered[display_columns],
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Inspect individual rule detail", expanded=True):
        render_rule_indicator_detail(result)


# ============================================================
# Rule Indicator Detail
# ============================================================


def render_rule_indicator_detail(result: Any) -> None:
    """Render a professional, display-only risk indicator card."""
    rule_results = _get_rule_results(result)
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
        if _rule_status(rule_result) == "TRIGGERED"
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
    indicator = _rule_indicator(selected_rule)
    category = str(getattr(selected_rule, "category", "—"))
    status = _rule_status(selected_rule)
    severity = _rule_severity(selected_rule)
    direction = _rule_direction(selected_rule)
    value = getattr(selected_rule, "value", None)
    threshold = getattr(selected_rule, "threshold", None)
    reason = getattr(selected_rule, "reason", None)

    status_text = _status_label(status)
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
            st.markdown(f"## {_format_indicator_value(value)}")
        with value_cols[1]:
            st.caption("Configured threshold")
            st.markdown(f"## {_format_indicator_value(threshold)}")

        if value is not None and threshold is not None:
            chart_data = pd.DataFrame(
                {
                    "Measure": ["Actual", "Threshold"],
                    "Value": [float(value), float(threshold)],
                }
            )
            st.bar_chart(chart_data, x="Measure", y="Value", height=170)

        meta_cols = st.columns(3)
        with meta_cols[0]:
            st.caption("Status")
            st.markdown(f"**{status_text}**")
        with meta_cols[1]:
            st.caption("Direction")
            st.markdown(f"**{direction}**")
        with meta_cols[2]:
            st.caption("Category")
            st.markdown(f"**{category}**")

        if reason:
            st.markdown("**Rationale**")
            st.write(reason)

    st.caption(
        "The card presents the Rule Engine output as-is; it does not recalculate "
        "thresholds, severity or assessment status."
    )
