"""Compact Rule Engine evidence visualization."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.components import render_section_header
from app.ui.results.helpers import (
    build_rule_dataframe,
    build_status_overview,
    get_rule_results,
    rule_status_counts,
    severity_counts,
    severity_rank,
)
from app.ui.results.rule_detail import render_rule_indicator_detail


_DOMAIN_LABELS = {
    "CP": "Customer Profile",
    "R": "Financial Analysis",
    "B": "Behavioural Analysis",
    "DS": "Debt Sustainability",
}


def _rule_domain(rule_id: str) -> str:
    """Map the deterministic rule identifier to its assessment macro-area."""
    rule_id = str(rule_id).upper()
    if rule_id.startswith("DS"):
        return _DOMAIN_LABELS["DS"]
    if rule_id.startswith("CP"):
        return _DOMAIN_LABELS["CP"]
    if rule_id.startswith("B"):
        return _DOMAIN_LABELS["B"]
    if rule_id.startswith("R"):
        return _DOMAIN_LABELS["R"]
    return "Other"


def _render_signal_overview(
    status_counts: dict[str, int],
    severity_counts_data: dict[str, int],
) -> None:
    """Show the two compact factual distributions of Rule Engine output."""
    overview_cols = st.columns(2)
    with overview_cols[0]:
        st.caption("Rule outcomes")
        st.bar_chart(
            build_status_overview(status_counts),
            x="Status",
            y="Rules",
            horizontal=True,
            height=155,
        )
    with overview_cols[1]:
        st.caption("Severity profile")
        severity_frame = pd.DataFrame(
            [{"Severity": key, "Rules": value} for key, value in severity_counts_data.items()]
        )
        st.bar_chart(
            severity_frame,
            x="Severity",
            y="Rules",
            horizontal=True,
            height=155,
        )


def _render_domain_coverage(dataframe: pd.DataFrame) -> None:
    """Show complete rule coverage by assessment macro-area."""
    coverage = dataframe.copy()
    coverage["Macro-area"] = coverage["Rule"].map(_rule_domain)

    domain_order = [
        "Customer Profile",
        "Financial Analysis",
        "Behavioural Analysis",
        "Debt Sustainability",
        "Other",
    ]

    summary = (
        coverage.groupby("Macro-area", dropna=False)
        .agg(
            Rules=("Rule", "count"),
            Triggered=("Status", lambda values: (values == "TRIGGERED").sum()),
            Not_triggered=("Status", lambda values: (values == "NOT_TRIGGERED").sum()),
            Not_evaluable=("Status", lambda values: (values == "NOT_EVALUABLE").sum()),
        )
        .reset_index()
    )
    summary["_domain_order"] = summary["Macro-area"].map(
        {name: index for index, name in enumerate(domain_order)}
    )
    summary = summary.sort_values("_domain_order").drop(columns="_domain_order")

    st.markdown("##### Rule Coverage by Assessment Area")
    st.caption(
        "Every configured deterministic rule is shown here, including rules that "
        "are not triggered by the selected scenario."
    )

    represented_areas = int(coverage["Macro-area"].nunique())
    configured_areas = len(_DOMAIN_LABELS)
    coverage_pct = (represented_areas / configured_areas * 100) if configured_areas else 0

    metric_cols = st.columns([1, 1, 2])
    with metric_cols[0]:
        st.metric("Rules in evidence", len(coverage))
    with metric_cols[1]:
        st.metric("Assessment areas", represented_areas)
    with metric_cols[2]:
        st.metric("Macro-area coverage", f"{coverage_pct:.0f}%")

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Macro-area": st.column_config.TextColumn("Assessment area", width="medium"),
            "Rules": st.column_config.NumberColumn("Rules", width="small"),
            "Triggered": st.column_config.NumberColumn("Triggered", width="small"),
            "Not_triggered": st.column_config.NumberColumn(
                "Not triggered", width="small"
            ),
            "Not_evaluable": st.column_config.NumberColumn(
                "Not evaluable", width="small"
            ),
        },
    )


def _render_rule_catalogue(dataframe: pd.DataFrame, status_counts: dict[str, int]) -> None:
    """Show filterable deterministic rule evidence."""
    filter_cols = st.columns([1.1, 1.1, 1.4, 1.2])
    with filter_cols[0]:
        status_options = ["All", "TRIGGERED", "NOT_TRIGGERED", "NOT_EVALUABLE"]
        selected_status = st.selectbox(
            "Status",
            status_options,
            index=0,
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
            "Severity", ["All", *severity_values], key="rule_catalogue_severity"
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
            "Category", ["All", *categories], key="rule_catalogue_category"
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

    st.caption(f"Showing {len(filtered)} of {len(dataframe)} rules.")
    display_columns = [
        "Rule", "Indicator", "Actual", "Threshold", "Status", "Severity", "Category"
    ]
    with st.container(border=True):
        if filtered.empty:
            st.info("No rules match the selected filters.")
        else:
            st.dataframe(filtered[display_columns], use_container_width=True, hide_index=True)


def render_risk_indicator_dashboard(result: Any) -> None:
    """Render the complete deterministic Rule Engine evidence view."""
    rule_results = get_rule_results(result)
    if not rule_results:
        return

    render_section_header(
        "Rule Engine Evidence",
        "Inspect the complete deterministic rule set and drill into individual rules when needed.",
    )

    dataframe = build_rule_dataframe(rule_results)
    status_counts = rule_status_counts(result)
    severity_counts_data = severity_counts(rule_results)

    _render_signal_overview(status_counts, severity_counts_data)
    _render_domain_coverage(dataframe)

    with st.expander("Complete rule catalogue & filters", expanded=True):
        _render_rule_catalogue(dataframe, status_counts)

    with st.expander("Individual rule detail", expanded=False):
        render_rule_indicator_detail(result)
