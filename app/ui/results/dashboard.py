"""Rule Engine evidence visualization driven by the credit assessment case."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.components import render_section_header
from app.ui.results.helpers import (
    build_rule_area_dataframe,
    build_status_overview,
    get_rule_results,
    get_rule_sections,
    rule_indicator,
    rule_severity,
    rule_status,
    rule_status_counts,
    severity_counts,
    severity_rank,
)
from app.ui.results.rule_detail import render_rule_indicator_detail


def _render_signal_overview(
    status_counts: dict[str, int],
    severity_counts_data: dict[str, int],
) -> None:
    """Show the factual distributions of deterministic Rule Engine output."""
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


def _section_indicators(section: Any) -> list[str]:
    """Return display-only key indicators from deterministic section evidence."""
    evidence = list(getattr(section, "evidence", []) or [])
    triggered = [
        rule_indicator(rule_result)
        for rule_result in evidence
        if rule_status(rule_result) == "TRIGGERED"
    ]
    if triggered:
        return triggered[:3]

    ranked = sorted(
        evidence,
        key=lambda rule_result: severity_rank(rule_severity(rule_result)),
        reverse=True,
    )
    return [rule_indicator(rule_result) for rule_result in ranked[:3]]


def _render_area_coverage(result: Any, dataframe: pd.DataFrame) -> None:
    """Render the four authoritative macro-areas as an analyst dashboard."""
    sections = get_rule_sections(result)
    if not sections:
        return

    st.markdown("##### Risk Assessment by Macro-Area")
    st.caption(
        "Each card reads the section status and evidence directly from the "
        "CreditAssessmentCase. The UI does not infer status from rule IDs."
    )

    area_columns = st.columns(2, gap="medium")
    for index, section in enumerate(sections):
        evidence = list(getattr(section, "evidence", []) or [])
        statuses = [rule_status(rule_result) for rule_result in evidence]
        triggered = statuses.count("TRIGGERED")
        not_triggered = statuses.count("NOT_TRIGGERED")
        not_evaluable = statuses.count("NOT_EVALUABLE")
        status = str(
            getattr(getattr(section, "status", None), "value", "NOT_EVALUABLE")
        )
        indicators = _section_indicators(section)

        with area_columns[index % 2].container(border=True):
            st.markdown(f"**{getattr(section, 'name', 'Assessment area')}**")
            st.caption(f"Section status: **{status}**")
            metric_cols = st.columns(4)
            metric_cols[0].metric("Rules", len(evidence))
            metric_cols[1].metric("Triggered", triggered)
            metric_cols[2].metric("Not triggered", not_triggered)
            metric_cols[3].metric("Not evaluable", not_evaluable)
            if indicators:
                st.caption("Key indicators")
                st.write(" · ".join(indicators))
            else:
                st.caption("Key indicators: —")

    summary = (
        dataframe.groupby("Assessment area", dropna=False)
        .agg(
            Rules=("Rule", "count"),
            Triggered=("Status", lambda values: (values == "TRIGGERED").sum()),
            Not_triggered=("Status", lambda values: (values == "NOT_TRIGGERED").sum()),
            Not_evaluable=("Status", lambda values: (values == "NOT_EVALUABLE").sum()),
        )
        .reset_index()
    )
    st.caption("Rule outcomes by macro-area")
    chart_data = summary.set_index("Assessment area")[[
        "Triggered",
        "Not_triggered",
        "Not_evaluable",
    ]]
    st.bar_chart(chart_data, height=210)


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
            "Severity", ["All", *severity_values], key="rule_catalogue_severity"
        )
    with filter_cols[2]:
        area_values = sorted(dataframe["Assessment area"].dropna().unique().tolist())
        selected_area = st.selectbox(
            "Assessment area", ["All", *area_values], key="rule_catalogue_area"
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
    if selected_sort == "Priority":
        filtered = filtered.sort_values("_priority", ascending=True)
    elif selected_sort == "Rule ID":
        filtered = filtered.sort_values("Rule", ascending=True)
    elif selected_sort == "Assessment area":
        filtered = filtered.sort_values(["Assessment area", "Rule"], ascending=True)
    else:
        filtered = filtered.sort_values(["Status", "Rule"], ascending=True)

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
    """Render complete deterministic Rule Engine evidence for the current case."""
    rule_results = get_rule_results(result)
    if not rule_results:
        return

    render_section_header(
        "Rule Engine Evidence",
        "Inspect the deterministic assessment across the four macro-areas, then drill into individual rules.",
    )

    dataframe = build_rule_area_dataframe(result)
    status_counts = rule_status_counts(result)
    severity_counts_data = severity_counts(rule_results)

    _render_signal_overview(status_counts, severity_counts_data)
    _render_area_coverage(result, dataframe)

    with st.expander("Complete rule catalogue & filters", expanded=False):
        _render_rule_catalogue(dataframe)

    with st.expander("Individual rule detail", expanded=False):
        render_rule_indicator_detail(result)
