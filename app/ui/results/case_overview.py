"""Detailed analyst view for the credit assessment case."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.results.helpers import format_indicator_value, rule_indicator, rule_status

_ASSESSMENT_AREA_ORDER = (
    "Customer Profile",
    "Financial Analysis",
    "Behavioural Analysis",
    "Debt Sustainability",
)


def _profile_value(data: Any, field: str, default: str = "Not available") -> str:
    value = data.get(field) if isinstance(data, dict) else getattr(data, field, None)
    if value is None or value == "":
        return default
    if hasattr(value, "value"):
        return str(value.value)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _profile_list(data: Any, field: str) -> list[Any]:
    value = data.get(field, []) if isinstance(data, dict) else getattr(data, field, [])
    return list(value or [])


def _section_status(section: Any) -> str:
    status = getattr(section, "status", None)
    return str(getattr(status, "value", status or "—")).replace("_", " ")


def _render_snapshot(section: Any) -> None:
    """Render the same deterministic snapshot for every macro-area."""
    evidence = list(getattr(section, "evidence", []) or [])
    statuses = [rule_status(rule) for rule in evidence]
    triggered = sum(status == "TRIGGERED" for status in statuses)
    not_evaluable = sum(status == "NOT_EVALUABLE" for status in statuses)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Assessment", _section_status(section))
    with col2:
        st.metric("Indicators", len(evidence))
    with col3:
        st.metric("Triggered", triggered)
    if not_evaluable:
        st.caption(f"{not_evaluable} indicator(s) are not evaluable with the available data.")


def _render_customer_evidence(section: Any) -> None:
    context = getattr(section, "context", {}) or {}
    if not context:
        st.info("Customer profile information is not available.")
        return
    st.markdown("**Key evidence**")
    profile_frame = pd.DataFrame([{
        "Company": _profile_value(context, "company_name"),
        "Legal form": _profile_value(context, "legal_form"),
        "Sector": _profile_value(context, "sector"),
        "Size class": _profile_value(context, "size_class"),
        "Geography": _profile_value(context, "geography"),
        "EWS Score Class": _profile_value(context, "ews_score_class"),
        "Forborne": _profile_value(context, "forborne"),
    }])
    st.dataframe(profile_frame, use_container_width=True, hide_index=True)
    relationship_col, ownership_col = st.columns(2)
    with relationship_col:
        st.markdown("**Banking relationship**")
        years = _profile_value(context, "relationship_years", "—")
        st.write(f"Relationship duration: **{years} years**")
        facilities = _profile_list(context, "historical_facilities")
        if facilities:
            for facility in facilities:
                st.write(f"• {facility}")
        else:
            st.caption("No historical facility information available.")
    with ownership_col:
        st.markdown("**Ownership & management**")
        shareholders = _profile_list(context, "shareholders")
        management = _profile_list(context, "management_members")
        for shareholder in shareholders:
            st.write(f"• Shareholder: {shareholder}")
        for member in management:
            st.write(f"• Management: {member}")
        if not shareholders and not management:
            st.caption("Ownership and management information not available.")


def _format_euro_amount(value: Any) -> str:
    """Format a numeric exposure as EUR without inventing missing values."""
    if value is None or value == "":
        return "Not available"
    try:
        return f"€{float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _render_behavioural_context(section: Any) -> None:
    """Render latest Centrale dei Rischi exposure context separately from rules."""
    context = getattr(section, "context", {}) or {}
    st.markdown("**Centrale dei Rischi — latest available month**")

    reference_month = _profile_value(context, "cr_reference_month")
    st.caption(f"Reference month: {reference_month}")

    total = context.get("total_utilized_system")
    revocable = context.get("utilized_revocable")
    term = context.get("utilized_term")
    self_liquidating = context.get("utilized_self_liquidating")

    metrics = [
        ("Total utilized at system level", total),
        ("Revocable lines", revocable),
        ("Term facilities", term),
        ("Self-liquidating facilities", self_liquidating),
    ]
    columns = st.columns(4)
    for column, (label, value) in zip(columns, metrics):
        with column:
            column.metric(label, _format_euro_amount(value))

    available_components = [
        value
        for value in (revocable, term, self_liquidating)
        if value is not None
    ]
    if total is not None and len(available_components) == 3:
        component_total = sum(float(value) for value in available_components)
        difference = float(total) - component_total
        if abs(difference) > 0.01:
            st.caption(
                "Note: the three facility categories do not reconcile to total "
                "utilized exposure "
                f"(difference: {_format_euro_amount(difference)})."
            )

    exposure_fields = (
        "total_utilized_system",
        "utilized_revocable",
        "utilized_term",
        "utilized_self_liquidating",
    )
    if not any(context.get(field) is not None for field in exposure_fields):
        st.info(
            "Centrale dei Rischi exposure amounts are not available for this case. "
            "Provide the latest reference month and utilization amounts in the input data."
        )


def _render_rule_evidence(section: Any) -> None:
    rows = [{
        "Indicator": rule_indicator(rule),
        "Value": format_indicator_value(getattr(rule, "value", None)),
        "Threshold": format_indicator_value(getattr(rule, "threshold", None)),
        "Status": rule_status(rule).replace("_", " "),
        "Rule": str(getattr(rule, "rule_id", "—")),
    } for rule in getattr(section, "evidence", []) or []]
    st.markdown("**Key evidence**")
    if not rows:
        st.info("No deterministic rule evidence is available for this macro-area.")
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_findings(section: Any) -> None:
    st.markdown("**Findings**")
    findings = list(getattr(section, "findings", []) or [])
    rendered = False
    for finding in findings:
        status = getattr(finding, "status", None)
        status_value = str(getattr(status, "value", status or "")).upper()
        if status_value not in {"", "TRIGGERED"}:
            continue
        text = getattr(finding, "text", None) or getattr(finding, "comment", None)
        if text:
            st.info(f"**{getattr(finding, 'rule_id', '—')}** — {text}")
            rendered = True
    if not rendered:
        st.caption("No triggered findings for this macro-area.")


def _render_quality_and_limitations(section: Any) -> None:
    st.markdown("**Data quality & limitations**")
    evidence = list(getattr(section, "evidence", []) or [])
    not_evaluable = sum(rule_status(rule) == "NOT_EVALUABLE" for rule in evidence)
    coverage = (len(evidence) - not_evaluable) / len(evidence) if evidence else 0.0
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Evidence coverage", f"{coverage:.0%}")
    with col2:
        st.metric("Not evaluable", not_evaluable)
    limitations = list(getattr(section, "limitations", []) or [])
    if limitations:
        for limitation in limitations:
            st.write(f"• {limitation}")
    else:
        st.caption("No explicit data limitations recorded.")


def _render_area(section: Any) -> None:
    """Render every macro-area with exactly the same analyst-facing structure."""
    _render_snapshot(section)
    st.divider()
    if section.name == "Customer Profile":
        _render_customer_evidence(section)
    elif section.name == "Behavioural Analysis":
        _render_behavioural_context(section)
        st.divider()
        _render_rule_evidence(section)
    else:
        _render_rule_evidence(section)
    st.divider()
    _render_findings(section)
    st.divider()
    _render_quality_and_limitations(section)


def render_credit_analysis_case(result: Any) -> None:
    """Render detailed analyst evidence using one consistent structure per macro-area."""
    credit_case = getattr(result, "credit_case", None)
    if credit_case is None:
        return
    st.markdown("### Detailed Assessment")
    st.caption(
        "Consistent analyst view across the four macro-areas: assessment snapshot, key evidence, "
        "findings, and data quality."
    )
    sections_by_name = {
        section.name: section for section in getattr(credit_case, "sections", []) or []
    }
    available_sections = [name for name in _ASSESSMENT_AREA_ORDER if name in sections_by_name]
    if not available_sections:
        st.info("No assessment areas are available for this case.")
        return
    tabs = st.tabs(available_sections)
    for tab, area_name in zip(tabs, available_sections):
        with tab:
            _render_area(sections_by_name[area_name])
