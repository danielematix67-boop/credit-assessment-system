"""Risk indicator dashboard orchestration."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.results.evidence import render_rule_evidence_matrix
from app.ui.results.helpers import (
    get_rule_results,
    rule_indicator,
    rule_severity,
    rule_status,
    rule_status_counts,
    severity_counts,
    severity_rank,
)
from app.ui.results.rule_detail import render_rule_indicator_detail


def _build_rule_dataframe(rule_results: list[Any]) -> pd.DataFrame:
    """Build presentation data from existing RuleResult objects only."""
    rows: list[dict[str, Any]] = []
    for rule_result in rule_results:
        rows.append(
            {
                "Rule": str(getattr(rule_result, "rule_id", "—")),
                "Indicator": rule_indicator(rule_result),
                "Actual": getattr(rule_result, "value", None),
                "Threshold": getattr(rule_result, "threshold", None),
                "Status": rule_status(rule_result),
                "Severity": rule_severity(rule_result),
                "Category": str(getattr(rule_result, "category", "—")),
            }
        )
    return pd.DataFrame(rows)


def _render_kpis(
    rule_results: list[Any],
    status_counts: dict[str, int],
    severity_counts_data: dict[str, int],
) -> None:
    metric_cols = st.columns(4)
    metrics = [
        ("Indicators", len(rule_results)),
        ("Triggered", status_counts["TRIGGERED"]),
        (
            "High / critical",
            severity_counts_data["HIGH"] + severity_counts_data["CRITICAL"],
        ),
        ("Not evaluable", status_counts["NOT_EVALUABLE"]),
    ]
    for column, (label, value) in zip(metric_cols, metrics):
        with column:
            st.metric(label, value)


def _render_decision_bridge(
    rule_results: list[Any],
    status_counts: dict[str, int],
    severity_counts_data: dict[str, int],
    result: Any,
) -> None:
    """Render a presentation-only bridge from rule outputs to assessment status."""
    st.markdown("#### Assessment Decision Bridge")
    st.caption(
        "A compact visual bridge between evaluated indicators, rule outcomes and the "
        "final deterministic monitoring assessment."
    )

    bridge_cols = st.columns([1, 0.22, 1, 0.22, 1])
    assessment = getattr(result, "assessment", None)
    assessment_status = str(
        getattr(getattr(assessment, "status", None), "value", "Unknown")
    )
    bridge_items = [
        ("Indicators evaluated", str(len(rule_results)), "Financial evidence"),
        ("Rules triggered", str(status_counts["TRIGGERED"]), "Risk evidence"),
        ("Final assessment", assessment_status, "Deterministic judgement"),
    ]

    for card_index, (label, value, description) in zip((0, 2, 4), bridge_items):
        with bridge_cols[card_index]:
            with st.container(border=True):
                st.caption(label)
                st.markdown(f"### {value}")
                st.caption(description)

    for arrow_index in (1, 3):
        with bridge_cols[arrow_index]:
            st.markdown(
                "<div style='text-align:center; padding-top:2.1rem; "
                "font-size:1.3rem;'>→</div>",
                unsafe_allow_html=True,
            )

    bridge_meta = st.columns(3)
    bridge_meta[0].caption(f"{len(rule_results)} indicators evaluated")
    bridge_meta[1].caption(
        f"{status_counts['TRIGGERED']} of {len(rule_results)} rules triggered"
    )
    bridge_meta[2].caption(
        f"{severity_counts_data['HIGH'] + severity_counts_data['CRITICAL']} "
        "high/critical severity outcomes"
    )
    st.caption(
        "This bridge is explanatory only. It does not recalculate thresholds, severity "
        "or assessment status."
    )


def _render_signal_overview(
    status_counts: dict[str, int],
    severity_counts_data: dict[str, int],
) -> None:
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
                "Severity": list(severity_counts_data.keys()),
                "Rules": list(severity_counts_data.values()),
            }
        )
        st.caption("Severity profile")
        st.bar_chart(severity_data, x="Severity", y="Rules", horizontal=True, height=190)

    st.caption(
        "Both views describe the factual Rule Engine output; they do not recalculate the assessment."
    )


def _render_rule_catalogue(dataframe: pd.DataFrame, status_counts: dict[str, int]) -> None:
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
            key=severity_rank,
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
            -severity_rank(str(row["Severity"])),
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


def render_risk_indicator_dashboard(result: Any) -> None:
    """Render the complete rule-outcome and indicator diagnostic dashboard."""
    rule_results = get_rule_results(result)
    if not rule_results:
        return

    st.subheader("Risk Indicator Dashboard")
    st.caption(
        "A structured view of the deterministic indicators, rule outcomes and risk severity."
    )

    dataframe = _build_rule_dataframe(rule_results)
    status_counts = rule_status_counts(result)
    severity_counts_data = severity_counts(rule_results)

    _render_kpis(rule_results, status_counts, severity_counts_data)
    _render_decision_bridge(
        rule_results,
        status_counts,
        severity_counts_data,
        result,
    )
    _render_signal_overview(status_counts, severity_counts_data)
    render_rule_evidence_matrix(result)
    _render_rule_catalogue(dataframe, status_counts)

    with st.expander("Inspect individual rule detail", expanded=True):
        render_rule_indicator_detail(result)
