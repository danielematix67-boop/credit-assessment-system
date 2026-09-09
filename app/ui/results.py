from typing import Any

import pandas as pd
import streamlit as st

from app.ui.charts import render_decision_path, render_risk_indicator_dashboard
from app.ui.credit_position import display_position_table
from app.ui.explainability import render_evidence_chain
from app.ui.report import render_report_tab
from app.ui.rule_logic import render_rule_logic


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
        '''<style>.ui-section-header{margin:1.7rem 0 .8rem 0;padding-bottom:.55rem;border-bottom:1px solid rgba(128,128,128,.20)}.ui-section-title{font-size:1.15rem;font-weight:700;letter-spacing:-.01em;line-height:1.3}.ui-section-description{margin-top:.18rem;color:rgba(128,128,128,.95);font-size:.82rem;line-height:1.45}div[data-testid="stMetric"]{padding:.15rem 0}</style>''',
        unsafe_allow_html=True,
    )


def render_assessment_overview(result: Any) -> None:
    """Show only the category-level overview; rule evidence is shown elsewhere."""
    rules = _rule_results(result)
    if not rules:
        return

    triggered = [rule for rule in rules if _status(rule) == "TRIGGERED"]
    _section_header(
        "Assessment Overview",
        "Category-level distribution of the risks identified by the deterministic Rule Engine.",
    )
    if triggered:
        category_counts = (
            pd.DataFrame(
                {"Category": [str(getattr(rule, "category", "—")) for rule in triggered]}
            )
            .value_counts("Category")
            .rename("Triggered rules")
            .reset_index()
            .sort_values("Triggered rules", ascending=True)
        )
        st.bar_chart(
            category_counts,
            x="Category",
            y="Triggered rules",
            horizontal=True,
            height=max(180, 55 * len(category_counts)),
        )
    else:
        st.success("No deterministic risk rules were triggered by the available information.")
    st.caption(
        "This chart summarises the rule outcomes by category; it does not recalculate the assessment."
    )
    render_rule_logic(result)


def render_audit_trail(result: Any, assessment_position: Any) -> None:
    """Keep technical provenance and traceability in one dedicated area."""
    with st.expander("Audit trail & methodology", expanded=False):
        st.caption(
            "Detailed calculation path, complete rule traceability and technical provenance."
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
    configured_model = None
    report_badge_kind, report_badge_label = resolve_report_badge(
        selected_reporting_mode,
        generator_used,
        configured_model,
    )

    render_report_tab(
        result=result,
        selected_reporting_mode=selected_reporting_mode,
        report_badge_kind=report_badge_kind,
        report_badge_label=report_badge_label,
        configured_model=configured_model,
    )
    render_assessment_overview(result)
    render_risk_indicator_dashboard(result)
    render_evidence_chain(result)
    render_audit_trail(result, assessment_position)
