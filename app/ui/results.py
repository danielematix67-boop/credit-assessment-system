from typing import Any

import pandas as pd
import streamlit as st

from app.ui.charts import render_decision_path, render_rule_assessment_summary
from app.ui.credit_position import display_position_table
from app.ui.report import render_report_tab


def resolve_report_badge(
    selected_reporting_mode: str,
    generator_used: str | None,
    configured_model: str | None = None,
) -> tuple[str, str]:
    """Resolve report provenance from the generator that actually produced it."""
    if generator_used == "FALLBACK":
        return "fallback", "Deterministic fallback"

    if generator_used == "PRIMARY":
        if selected_reporting_mode == "Gemini + Fallback":
            return "ai", "AI-generated — Gemini"
        if selected_reporting_mode == "Ollama + Fallback":
            return "ai", "AI-generated — Local LLM"

    return "det", "Deterministic — Rule Engine"


def _rule_results(result: Any) -> list[Any]:
    """Read RuleResult objects from the deterministic assessment."""
    assessment = getattr(result, "assessment", None)
    return list(getattr(assessment, "rule_results", []) or [])


def _status(rule: Any) -> str:
    value = getattr(rule, "status", None)
    return str(getattr(value, "value", value or ""))


def _severity(rule: Any) -> str:
    value = getattr(rule, "severity", None)
    return str(getattr(value, "value", value or ""))


def _format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _section_header(title: str, description: str) -> None:
    """Render a consistent visual section header."""
    st.markdown(
        f"""
        <div class="ui-section-header">
            <div class="ui-section-title">{title}</div>
            <div class="ui-section-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _apply_results_styles() -> None:
    """Add lightweight styling for the results hierarchy."""
    st.markdown(
        """
        <style>
        .ui-section-header {
            margin: 1.7rem 0 0.8rem 0;
            padding-bottom: 0.55rem;
            border-bottom: 1px solid rgba(128, 128, 128, 0.20);
        }
        .ui-section-title {
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            line-height: 1.3;
        }
        .ui-section-description {
            margin-top: 0.18rem;
            color: rgba(128, 128, 128, 0.95);
            font-size: 0.82rem;
            line-height: 1.45;
        }
        .results-lead {
            margin: 0.2rem 0 1.0rem 0;
            color: rgba(128, 128, 128, 0.95);
            font-size: 0.88rem;
            line-height: 1.5;
        }
        div[data-testid="stMetric"] {
            padding: 0.15rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_decision_evidence(result: Any) -> None:
    """Show the deterministic evidence an operator needs to validate the judgement."""
    rules = _rule_results(result)
    triggered = [rule for rule in rules if _status(rule) == "TRIGGERED"]

    _section_header(
        "Decision Evidence",
        "Deterministic rules supporting the final credit judgement.",
    )

    if not triggered:
        st.success("No risk rules were triggered by the available financial information.")
        return

    severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    triggered = sorted(
        triggered,
        key=lambda rule: severity_rank.get(_severity(rule).upper(), 99),
    )

    rows = []
    for rule in triggered:
        category = getattr(rule, "category", "—")
        category = getattr(category, "value", str(category))
        rows.append(
            {
                "Rule": str(getattr(rule, "rule_id", "—")),
                "Indicator": str(getattr(rule, "rule_name", "—")),
                "Actual": _format_value(getattr(rule, "value", None)),
                "Threshold": _format_value(getattr(rule, "threshold", None)),
                "Severity": _severity(rule) or "—",
                "Category": str(category),
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


def render_audit_trail(result: Any, assessment_position: Any) -> None:
    """Keep technical and audit information available without competing with the operator flow."""
    with st.expander("Audit trail & methodology", expanded=False):
        st.caption("Detailed calculation path, complete rule evidence and technical provenance.")

        st.markdown("#### Assessment flow")
        render_decision_path(result)

        st.markdown("#### Complete rule evidence")
        render_rule_assessment_summary(result)

        st.markdown("#### Credit data used")
        if assessment_position is not None:
            display_position_table(assessment_position)
        else:
            st.info("The assessed credit position is not available.")

        st.markdown("#### Methodology")
        st.write(
            "The Rule Engine is the sole authority for assessment status, rule outcomes, severity and thresholds. "
            "The Analysis layer organises the resulting findings. "
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
                ("Reporting time", f"{getattr(metadata, 'reporting_elapsed_time', 0.0):.3f} s"),
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
    """Render results in the same order used by a credit-monitoring operator."""
    if result is None:
        return

    _apply_results_styles()
    st.divider()

    generator_used = getattr(result, "report_generator_used", None)
    configured_model = None
    report_badge_kind, report_badge_label = resolve_report_badge(
        selected_reporting_mode=selected_reporting_mode,
        generator_used=generator_used,
        configured_model=configured_model,
    )

    with st.container(border=True):
        render_report_tab(
            result=result,
            selected_reporting_mode=selected_reporting_mode,
            report_badge_kind=report_badge_kind,
            report_badge_label=report_badge_label,
            configured_model=configured_model,
        )

    render_decision_evidence(result)
    render_audit_trail(result, assessment_position)
