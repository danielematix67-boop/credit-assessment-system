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


def _render_rule_catalogue(dataframe: pd.DataFrame, status_counts: dict[str, int]) -> None:
    """Show filterable deterministic rule evidence."""
    filter_cols = st.columns([1.1, 1.1, 1.4, 1.2])
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
    """Render a compact deterministic Rule Engine evidence view."""
    rule_results = get_rule_results(result)
    if not rule_results:
        return

    render_section_header(
        "Rule Engine Evidence",
        "Inspect deterministic indicator outcomes and drill into individual rules when needed.",
    )

    dataframe = build_rule_dataframe(rule_results)
    status_counts = rule_status_counts(result)
    severity_counts_data = severity_counts(rule_results)

    _render_signal_overview(status_counts, severity_counts_data)

    with st.expander("Rule catalogue & filters", expanded=False):
        _render_rule_catalogue(dataframe, status_counts)

    with st.expander("Individual rule detail", expanded=False):
        render_rule_indicator_detail(result)
