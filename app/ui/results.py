from typing import Any

import streamlit as st

from app.ui.charts import render_decision_path, render_risk_indicator_dashboard
from app.ui.credit_position import display_position_table
from app.ui.report import render_report_tab


def resolve_report_badge(
    selected_reporting_mode: str,
    generator_used: str | None,
    configured_model: str | None = None,
) -> tuple[str, str]:
    if generator_used == "FALLBACK":
        return "fallback", "Deterministic fallback"
    if generator_used == "PRIMARY":
        if selected_reporting_mode == "Gemini + Fallback":
            return "ai", "AI-generated — Gemini"
        if selected_reporting_mode == "Ollama + Fallback":
            return "ai", "AI-generated — Local LLM"
    return "det", "Deterministic — Rule Engine"


def _rule_results(result: Any) -> list[Any]:
    assessment = getattr(result, "assessment", None)
    return list(getattr(assessment, "rule_results", []) or [])


def _status(rule: Any) -> str:
    value = getattr(rule, "status", None)
    return str(getattr(value, "value", value or ""))


def _section_header(title: str, description: str) -> None:
    st.markdown(
        f'''<div class="ui-section-header"><div class="ui-section-title">{title}</div><div class="ui-section-description">{description}</div></div>''',
        unsafe_allow_html=True,
    )


def _apply_results_styles() -> None:
    st.markdown(
        '''<style>.ui-section-header{margin:1.7rem 0 .8rem 0;padding-bottom:.55rem;border-bottom:1px solid rgba(128,128,128,.20)}.ui-section-title{font-size:1.15rem;font-weight:700;letter-spacing:-.01em;line-height:1.3}.ui-section-description{margin-top:.18rem;color:rgba(128,128,128,.95);font-size:.82rem;line-height:1.45}</style>''',
        unsafe_allow_html=True,
    )


def render_assessment_overview(result: Any) -> None:
    """Show only a concise assessment summary without risk-category duplication."""
    rules = _rule_results(result)
    if not rules:
        return

    assessment = getattr(result, "assessment", None)
    status_obj = getattr(assessment, "status", None)
    status = str(getattr(status_obj, "value", status_obj or "Unknown"))
    triggered = sum(_status(rule) == "TRIGGERED" for rule in rules)

    _section_header(
        "Assessment Overview",
        "Concise summary of the deterministic assessment. Detailed rule findings are shown only in the Risk Indicator Dashboard.",
    )
    cols = st.columns(2)
    with cols[0]:
        st.metric("Assessment status", status)
    with cols[1]:
        st.metric("Triggered rules", triggered)


def render_audit_trail(result: Any, assessment_position: Any) -> None:
    """Keep technical provenance separate from the main findings view."""
    with st.expander("Audit trail & methodology", expanded=False):
        st.caption(
            "Technical provenance is kept here. Detailed rule findings are shown only "
            "in the Risk Indicator Dashboard to avoid duplicate evidence."
        )
        st.markdown("#### Assessment flow")
        render_decision_path(result)
        st.markdown("#### Credit data used")
        if assessment_position is not None:
            display_position_table(assessment_position)
        else:
            st.info("The assessed credit position is not available.")
        st.markdown("#### Methodology")
        st.write(
            "The Rule Engine is the sole authority for assessment status, rule outcomes, "
            "severity and thresholds. The Analysis layer organises the resulting findings. "
            "The Reporting layer converts the structured result into the Executive Report. "
            "Gemini and Ollama can generate narrative text, but cannot change the credit judgement."
        )
        metadata = getattr(result, "execution_metadata", None)
        if metadata is not None:
            st.markdown("#### Execution")
            cols = st.columns(4)
            values = [
                ("Generator", getattr(metadata, "generator_used", "—") or "—"),
                ("Fallback", "Yes" if getattr(metadata, "fallback_used", False) else "No"),
                (
                    "Reporting time",
                    f"{getattr(metadata, 'reporting_elapsed_time', 0.0):.3f} s",
                ),
                ("Total time", f"{getattr(metadata, 'total_elapsed_time', 0.0):.3f} s"),
            ]
            for column, (label, value) in zip(cols, values):
                with column:
                    st.caption(label)
                    st.write(value)


def render_results(
    result: Any,
    assessment_position: Any,
    selected_reporting_mode: str,
) -> None:
    if result is None:
        return

    _apply_results_styles()
    st.divider()
    generator_used = getattr(result, "report_generator_used", None)
    report_badge_kind, report_badge_label = resolve_report_badge(
        selected_reporting_mode,
        generator_used,
    )

    render_report_tab(
        result=result,
        selected_reporting_mode=selected_reporting_mode,
        report_badge_kind=report_badge_kind,
        report_badge_label=report_badge_label,
        configured_model=None,
    )
    render_assessment_overview(result)
    render_risk_indicator_dashboard(result)
    render_audit_trail(result, assessment_position)
