"""Detailed analyst view for the credit assessment case."""

from typing import Any

import pandas as pd
import streamlit as st

from app.ui.results.financial_analysis import (
    render_behavioural_analysis,
    render_debt_analysis,
    render_financial_analysis,
)


def _profile_value(data: Any, field: str, default: str = "Not available") -> str:
    if isinstance(data, dict):
        value = data.get(field)
    else:
        value = getattr(data, field, None)
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _profile_completeness(data: Any) -> tuple[int, int]:
    fields = (
        "company_name",
        "legal_form",
        "sector",
        "size_class",
        "geography",
        "relationship_years",
        "historical_facilities",
        "active_ews",
        "previous_restructuring",
        "business_history_years",
    )
    available = sum(
        _profile_value(data, field, "") not in {"", "Not available"}
        for field in fields
    )
    return available, len(fields)


def _profile_list(data: Any, field: str) -> list[Any]:
    if isinstance(data, dict):
        value = data.get(field, [])
    else:
        value = getattr(data, field, [])
    return list(value or [])


def _render_customer_profile(section: Any) -> None:
    """Render customer context without duplicating Rule Engine evidence."""
    context = getattr(section, "context", {}) or {}

    if not context:
        st.info("Customer profile information is not available.")
        return

    available, total = _profile_completeness(context)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Profile information", f"{available}/{total}")
    with col2:
        relationship_years = _profile_value(context, "relationship_years", "—")
        st.metric("Banking relationship", f"{relationship_years} years")
    with col3:
        st.metric("Historical facilities", len(_profile_list(context, "historical_facilities")))

    st.markdown("**Company & anagraphic profile**")
    profile_frame = pd.DataFrame(
        [
            {
                "Company": _profile_value(context, "company_name"),
                "Legal form": _profile_value(context, "legal_form"),
                "Sector": _profile_value(context, "sector"),
                "Size class": _profile_value(context, "size_class"),
                "Geography": _profile_value(context, "geography"),
            }
        ]
    )
    st.dataframe(profile_frame, use_container_width=True, hide_index=True)

    relationship_col, ownership_col = st.columns(2)
    with relationship_col:
        st.markdown("**Banking relationship**")
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
        if shareholders:
            st.write("Shareholders")
            for shareholder in shareholders:
                st.write(f"• {shareholder}")
        if management:
            st.write("Management")
            for member in management:
                st.write(f"• {member}")
        if not shareholders and not management:
            st.caption("Ownership and management information not available.")


def _render_limitations(section: Any) -> None:
    """Render limitations inline because the parent already controls disclosure."""
    limitations = list(getattr(section, "limitations", []) or [])
    if not limitations:
        return
    st.markdown("**Limitations**")
    for limitation in limitations:
        st.write(f"• {limitation}")


def _render_data_quality_overview(credit_case: Any) -> None:
    """Show evidence coverage as a technical/audit view."""
    sections = list(getattr(credit_case, "sections", []) or [])
    total_evidence = sum(len(getattr(section, "evidence", []) or []) for section in sections)
    evaluable_evidence = sum(
        sum(
            str(getattr(getattr(rule, "status", None), "value", getattr(rule, "status", ""))).upper()
            != "NOT_EVALUABLE"
            for rule in getattr(section, "evidence", [])
        )
        for section in sections
    )
    not_evaluable_evidence = total_evidence - evaluable_evidence
    sections_with_limitations = sum(
        bool(getattr(section, "limitations", [])) for section in sections
    )
    coverage = evaluable_evidence / total_evidence if total_evidence else 0.0

    st.markdown("**Data & Evidence Quality**")
    st.caption(
        "Technical coverage view for auditability. Missing data remain explicit limitations and do not become a synthetic risk score."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Evidence items", total_evidence)
    with col2:
        st.metric("Not evaluable", not_evaluable_evidence)
    with col3:
        st.metric("Evidence coverage", f"{coverage:.0%}")

    quality_rows = []
    for section in sections:
        evidence = list(getattr(section, "evidence", []) or [])
        total = len(evidence)
        evaluable = sum(
            str(getattr(getattr(rule, "status", None), "value", getattr(rule, "status", ""))).upper()
            != "NOT_EVALUABLE"
            for rule in evidence
        )
        quality_rows.append(
            {
                "Macro-area": section.name,
                "Evidence": total,
                "Evaluable": evaluable,
                "Not evaluable": total - evaluable,
                "Coverage": evaluable / total if total else 0.0,
                "Limitations": len(getattr(section, "limitations", []) or []),
            }
        )

    quality_frame = pd.DataFrame(quality_rows)
    if quality_frame.empty:
        st.info("No evidence items are available for this case.")
        return

    display_frame = quality_frame.copy()
    display_frame["Coverage"] = display_frame["Coverage"].map(lambda value: f"{value:.0%}")
    st.dataframe(display_frame, use_container_width=True, hide_index=True)

    if sections_with_limitations:
        st.info(
            f"{sections_with_limitations} of {len(sections)} macro-areas contain explicit data limitations."
        )


def render_credit_analysis_case(result: Any) -> None:
    """Render detailed analyst evidence without repeating the executive assessment."""
    credit_case = getattr(result, "credit_case", None)
    if credit_case is None:
        return

    st.markdown("### Detailed Assessment")
    st.caption(
        "Analyst and audit detail only. Overall status and macro-area outcomes are presented above; this section focuses on context, indicators, findings and limitations."
    )

    _render_data_quality_overview(credit_case)

    for section in credit_case.sections:
        st.markdown(f"#### {section.name}")

        if section.name == "Financial Analysis":
            render_financial_analysis(section)
        elif section.name == "Behavioural Analysis":
            render_behavioural_analysis(section)
        elif section.name == "Debt Sustainability":
            render_debt_analysis(section)
        elif section.name == "Customer Profile":
            _render_customer_profile(section)

        _render_limitations(section)
