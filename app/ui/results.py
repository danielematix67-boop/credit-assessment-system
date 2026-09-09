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


def _status_class(status: str) -> str:
    return {
        "NORMAL": "normal",
        "ATTENTION": "attention",
        "CRITICAL": "critical",
    }.get(status.upper(), "neutral")


def _apply_results_styles() -> None:
    st.markdown(
        """
        <style>
        .results-divider {
            height: 1px;
            margin: 0 0 1.35rem 0;
            background: linear-gradient(90deg, transparent, rgba(128,128,128,.28), transparent);
        }

        .ui-section-header {
            margin: 1.8rem 0 .8rem 0;
            padding-bottom: .65rem;
            border-bottom: 1px solid rgba(128,128,128,.18);
        }

        .ui-section-title {
            font-size: 1.18rem;
            font-weight: 720;
            letter-spacing: -.015em;
            line-height: 1.3;
        }

        .ui-section-description {
            margin-top: .22rem;
            color: rgba(128,128,128,.95);
            font-size: .82rem;
            line-height: 1.45;
        }

        .assessment-hero {
            position: relative;
            overflow: hidden;
            margin: .15rem 0 1.1rem 0;
            padding: 1.35rem 1.5rem 1.25rem 1.5rem;
            border: 1px solid rgba(128,128,128,.20);
            border-radius: 1rem;
            background: linear-gradient(135deg, rgba(128,128,128,.045), rgba(128,128,128,.015));
            box-shadow: 0 8px 26px rgba(0,0,0,.035);
        }

        .assessment-hero::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: var(--det-color, #2563eb);
        }

        .assessment-hero-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
        }

        .assessment-kicker {
            color: rgba(128,128,128,.95);
            font-size: .72rem;
            font-weight: 750;
            letter-spacing: .10em;
            text-transform: uppercase;
        }

        .assessment-title {
            margin-top: .18rem;
            font-size: 1.55rem;
            font-weight: 760;
            letter-spacing: -.025em;
            line-height: 1.2;
        }

        .assessment-status {
            display: inline-flex;
            align-items: center;
            gap: .42rem;
            padding: .42rem .78rem;
            border-radius: 999px;
            border: 1px solid transparent;
            font-size: .76rem;
            font-weight: 760;
            letter-spacing: .04em;
            white-space: nowrap;
        }

        .assessment-status::before {
            content: "";
            width: .48rem;
            height: .48rem;
            border-radius: 50%;
            background: currentColor;
        }

        .assessment-status.normal {
            color: #15803d;
            background: rgba(21,128,61,.08);
            border-color: rgba(21,128,61,.20);
        }

        .assessment-status.attention {
            color: #b45309;
            background: rgba(180,83,9,.09);
            border-color: rgba(180,83,9,.22);
        }

        .assessment-status.critical {
            color: #b91c1c;
            background: rgba(185,28,28,.08);
            border-color: rgba(185,28,28,.20);
        }

        .assessment-status.neutral {
            color: #6b7280;
            background: rgba(107,114,128,.08);
            border-color: rgba(107,114,128,.18);
        }

        .assessment-subtitle {
            margin-top: .7rem;
            color: rgba(128,128,128,.95);
            font-size: .86rem;
            line-height: 1.5;
        }

        .results-kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .7rem;
            margin: .8rem 0 1.25rem 0;
        }

        .results-kpi {
            min-width: 0;
            padding: .85rem .95rem;
            border: 1px solid rgba(128,128,128,.18);
            border-radius: .8rem;
            background: rgba(128,128,128,.025);
        }

        .results-kpi-label {
            color: rgba(128,128,128,.90);
            font-size: .70rem;
            font-weight: 650;
            letter-spacing: .025em;
            text-transform: uppercase;
        }

        .results-kpi-value {
            margin-top: .2rem;
            font-size: 1.15rem;
            font-weight: 740;
            line-height: 1.2;
        }

        .results-kpi-value.risk {
            color: #b91c1c;
        }

        .results-kpi-value.warning {
            color: #b45309;
        }

        .results-kpi-value.good {
            color: #15803d;
        }

        @media (max-width: 760px) {
            .assessment-hero-top {
                flex-direction: column;
            }

            .results-kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_results_header(result: Any) -> None:
    """Render the executive assessment header without changing assessment logic."""
    assessment = getattr(result, "assessment", None)
    status_obj = getattr(assessment, "status", None)
    status = str(getattr(status_obj, "value", status_obj or "Unknown"))
    rules = _rule_results(result)
    triggered = sum(_status(rule) == "TRIGGERED" for rule in rules)
    not_evaluable = sum(_status(rule) == "NOT_EVALUABLE" for rule in rules)
    status_class = _status_class(status)

    st.markdown(
        f"""
        <div class="assessment-hero">
            <div class="assessment-hero-top">
                <div>
                    <div class="assessment-kicker">Credit Risk Monitoring</div>
                    <div class="assessment-title">Executive Credit Assessment</div>
                </div>
                <div class="assessment-status {status_class}">{status}</div>
            </div>
            <div class="assessment-subtitle">
                Deterministic assessment based on the configured Rule Engine, with the
                reporting layer used only to provide an executive narrative.
            </div>
        </div>
        <div class="results-kpi-grid">
            <div class="results-kpi">
                <div class="results-kpi-label">Rules evaluated</div>
                <div class="results-kpi-value">{len(rules)}</div>
            </div>
            <div class="results-kpi">
                <div class="results-kpi-label">Triggered rules</div>
                <div class="results-kpi-value {'risk' if triggered else 'good'}">{triggered}</div>
            </div>
            <div class="results-kpi">
                <div class="results-kpi-label">Not evaluable</div>
                <div class="results-kpi-value {'warning' if not_evaluable else 'good'}">{not_evaluable}</div>
            </div>
            <div class="results-kpi">
                <div class="results-kpi-label">Decision source</div>
                <div class="results-kpi-value">Rule Engine</div>
            </div>
        </div>
        """,
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
    st.markdown('<div class="results-divider"></div>', unsafe_allow_html=True)
    render_results_header(result)

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
