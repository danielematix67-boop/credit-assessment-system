"""Compact deterministic Rule Engine evidence dashboard."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.components import render_section_header
from app.ui.results.helpers import (
    build_rule_area_dataframe,
    get_rule_results,
    get_rule_sections,
    rule_indicator,
    rule_severity,
    rule_status,
    severity_rank,
)
from app.ui.results.rule_detail import render_rule_indicator_detail


def _section_indicators(section: Any) -> list[str]:
    """Return display-only key indicators from deterministic section evidence."""
    evidence = list(getattr(section, "evidence", []) or [])
    triggered = [
        rule_indicator(rule_result)
        for rule_result in evidence
        if rule_status(rule_result) == "TRIGGERED"
    ]
    if triggered:
        return triggered[:4]
    ranked = sorted(
        evidence,
        key=lambda rule_result: severity_rank(rule_severity(rule_result)),
        reverse=True,
    )
    return [rule_indicator(rule_result) for rule_result in ranked[:4]]


def _render_area_cards(result: Any) -> None:
    """Render the authoritative macro-area status cards."""
    sections = get_rule_sections(result)
    if not sections:
        return

    st.markdown("##### Assessment by Macro-Area")
    st.caption("Deterministic section status and rule coverage.")
    area_columns = st.columns(2, gap="medium")
    for index, section in enumerate(sections):
        evidence = list(getattr(section, "evidence", []) or [])
        statuses = [rule_status(rule_result) for rule_result in evidence]
        triggered = statuses.count("TRIGGERED")
        not_evaluable = statuses.count("NOT_EVALUABLE")
        status = str(getattr(getattr(section, "status", None), "value", "NOT_EVALUABLE"))
        indicators = _section_indicators(section)
        with area_columns[index % 2].container(border=True):
            st.markdown(f"**{getattr(section, 'name', 'Assessment area')}**")
            st.caption(
                f"{status} · {len(evidence)} rules · {triggered} triggered · "
                f"{not_evaluable} not evaluable"
            )
            if indicators:
                st.caption("Key indicators")
                st.write(" · ".join(indicators))


def _render_rule_catalogue(dataframe: pd.DataFrame) -> None:
    """Show filterable deterministic rule evidence."""
    filter_cols = st.columns([1.1, 1.1, 1.4, 1.2])
    with filter_cols[0]:
        selected_status = st.selectbox(
            "Status",
            ["All", "TRIGGERED", "NOT_TRIGGERED", "NOT_EVALUABLE"],
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
        area_values = sorted(dataframe["Assessment area"].dropna().unique().tolist())
        selected_area = st.selectbox(
            "Assessment area",
            ["All", *area_values],
            key="rule_catalogue_area",
        )
    with filter_cols[3]:
        selected_sort = st.selectbox(
            "Sort by",
            ["Priority", "Rule ID", "Assessment area", "Status"],
            key="rule_catalogue_sort",
        )

    filtered = dataframe.copy()
    if selected_status != "All":
        filtered = filtered[filtered["Status"] == selected_status]
    if selected_severity != "All":
        filtered = filtered[filtered["Severity"] == selected_severity]
    if selected_area != "All":
        filtered = filtered[filtered["Assessment area"] == selected_area]

    filtered["_priority"] = filtered.apply(
        lambda row: (
            0 if row["Status"] == "TRIGGERED" else 1,
            -severity_rank(str(row["Severity"])),
            str(row["Rule"]),
        ),
        axis=1,
    )
    sort_map = {
        "Priority": ("_priority",),
        "Rule ID": ("Rule",),
        "Assessment area": ("Assessment area", "Rule"),
        "Status": ("Status", "Rule"),
    }
    filtered = filtered.sort_values(list(sort_map[selected_sort]), ascending=True)
    st.caption(f"Showing {len(filtered)} of {len(dataframe)} rules.")
    display_columns = [
        "Assessment area",
        "Rule",
        "Indicator",
        "Actual",
        "Threshold",
        "Status",
        "Severity",
        "Category",
    ]
    with st.container(border=True):
        if filtered.empty:
            st.info("No rules match the selected filters.")
        else:
            st.dataframe(filtered[display_columns], use_container_width=True, hide_index=True)


def render_risk_indicator_dashboard(result: Any) -> None:
    """Render the compact deterministic evidence layer."""
    rule_results = get_rule_results(result)
    if not rule_results:
        return
    render_section_header("Rule Engine Evidence", "Deterministic evidence across the four macro-areas.")
    dataframe = build_rule_area_dataframe(result)
    _render_area_cards(result)
    with st.expander("Rule catalogue & filters", expanded=False):
        _render_rule_catalogue(dataframe)
    with st.expander("Individual rule detail", expanded=False):
        render_rule_indicator_detail(result)
