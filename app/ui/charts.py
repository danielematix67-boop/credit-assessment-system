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
    """Render a scalable dashboard for rule outcomes and risk categories."""
    rule_results = _get_rule_results(result)
    if not rule_results:
        return

    st.subheader("Risk Indicator Dashboard")
    st.caption(
        "Start from the overall rule outcome, then narrow the rule catalogue by "
        "status, severity or category when you need to investigate specific drivers."
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

    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Rules evaluated", len(rule_results))
    with metric_cols[1]:
        st.metric("Triggered", status_counts["TRIGGERED"])
    with metric_cols[2]:
        st.metric("Not triggered", status_counts["NOT_TRIGGERED"])
    with metric_cols[3]:
        st.metric("Not evaluable", status_counts["NOT_EVALUABLE"])

    triggered = dataframe[dataframe["Status"] == "TRIGGERED"]

    if triggered.empty:
        st.success("No risk indicators breached their configured thresholds.")
    else:
        st.markdown("#### Active Risk Drivers")
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

    st.markdown("#### Rule Catalogue")
    st.caption(
        "Filter the evaluated rules before opening the detailed table. "
        "This keeps the interface usable as the rule library grows."
    )

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


# ============================================================
# Risk Driver Map
# ============================================================


def render_risk_driver_map(result: Any) -> None:
    """Show the linkage from triggered rules to risk categories and final assessment."""
    rule_results = _get_rule_results(result)
    triggered_rules = [
        rule_result
        for rule_result in rule_results
        if _rule_status(rule_result) == "TRIGGERED"
    ]

    if not triggered_rules:
        st.subheader("Risk Driver Map")
        st.success("No triggered rules were identified, so no active risk drivers are present.")
        return

    assessment = getattr(result, "assessment", None)
    assessment_status = str(
        getattr(
            getattr(assessment, "status", None),
            "value",
            "Unknown",
        )
    )

    grouped: dict[str, list[Any]] = {}
    for rule_result in triggered_rules:
        category = str(getattr(rule_result, "category", "—"))
        grouped.setdefault(category, []).append(rule_result)

    st.subheader("Risk Driver Map")
    st.caption(
        "This view links each triggered rule to its risk category and shows how the "
        "identified drivers support the final assessment outcome."
    )

    category_items = sorted(
        grouped.items(),
        key=lambda item: (
            -max(_severity_rank(_rule_severity(rule)) for rule in item[1]),
            -len(item[1]),
            item[0],
        ),
    )

    cols_per_row = 2
    for start in range(0, len(category_items), cols_per_row):
        row_items = category_items[start : start + cols_per_row]
        columns = st.columns(len(row_items))

        for column, (category, category_rules) in zip(columns, row_items):
            with column:
                with st.container(border=True):
                    highest_severity = max(
                        (_rule_severity(rule) for rule in category_rules),
                        key=_severity_rank,
                    )
                    st.markdown(f"**{category.upper()}**")
                    st.metric("Triggered rules", len(category_rules))
                    st.caption(f"Highest severity: {highest_severity}")

                    for rule_result in category_rules:
                        rule_id = str(getattr(rule_result, "rule_id", "—"))
                        indicator = _rule_indicator(rule_result)
                        value = getattr(rule_result, "value", None)
                        threshold = getattr(rule_result, "threshold", None)

                        st.markdown(f"**{rule_id}** · {indicator}")
                        if value is not None and threshold is not None:
                            st.caption(
                                f"Actual {float(value):g} vs threshold {float(threshold):g}"
                            )
                        st.caption(f"Severity: {_rule_severity(rule_result)}")

    st.markdown("#### Risk Drivers → Assessment")
    assessment_cols = st.columns(3)
    with assessment_cols[0]:
        st.metric("Active risk categories", len(grouped))
    with assessment_cols[1]:
        st.metric("Triggered rules", len(triggered_rules))
    with assessment_cols[2]:
        st.metric("Final assessment", assessment_status)

    st.caption(
        "Interpretation: each active category is supported by one or more triggered "
        "deterministic rules; together these rule findings provide the evidence base "
        "for the final assessment."
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
    indicator = _rule_indicator(selected_rule)
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

    st.markdown(f"**Indicator:** {indicator}")

    if value is None or threshold is None:
        st.info(
            "The quantitative comparison cannot be displayed because "
            "the rule result does not contain both a value and a threshold."
        )
    else:
        value_float = float(value)
        threshold_float = float(threshold)
        gap = value_float - threshold_float

        comparison_data = pd.DataFrame(
            {
                "Metric": ["Actual value", "Threshold"],
                "Value": [value_float, threshold_float],
            }
        )

        st.markdown("##### Actual vs Threshold")
        st.bar_chart(
            comparison_data,
            x="Metric",
            y="Value",
            horizontal=True,
            height=190,
        )

        value_cols = st.columns(3)

        with value_cols[0]:
            st.metric("Actual value", f"{value_float:g}")

        with value_cols[1]:
            st.metric("Threshold", f"{threshold_float:g}")

        with value_cols[2]:
            st.metric("Threshold gap", f"{gap:+g}")

        if status == "TRIGGERED":
            st.warning(
                f"The actual value differs from the configured threshold by "
                f"{gap:+g}. This rule is therefore recorded as TRIGGERED by the Rule Engine."
            )
        elif status == "NOT_TRIGGERED":
            st.success(
                f"The actual value differs from the configured threshold by "
                f"{gap:+g}. This rule is recorded as NOT_TRIGGERED by the Rule Engine."
            )

    if reason:
        st.markdown("**Why did this rule produce this result?**")
        st.info(reason)
