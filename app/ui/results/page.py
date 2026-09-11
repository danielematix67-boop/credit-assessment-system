from dataclasses import replace
from typing import Any

import streamlit as st

from app.ui.results.case_overview import render_credit_analysis_case
from app.ui.results.dashboard import render_risk_indicator_dashboard
from app.ui.results.decision_bridge import render_decision_path
from app.ui.results.executive_synthesis import render_executive_synthesis
from app.ui.results.final_assessment import render_final_assessment
from app.ui.results.helpers import get_rule_results, rule_status
from app.ui.results.risk_drivers import render_risk_driver_overview


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
        .results-divider { height: 1px; margin: 0 0 1.1rem 0; background: linear-gradient(90deg, transparent, rgba(128,128,128,.28), transparent); }
        .assessment-hero { position: relative; overflow: hidden; margin: .15rem 0 .8rem 0; padding: 1.2rem 1.35rem 1.1rem 1.35rem; border: 1px solid rgba(128,128,128,.20); border-radius: 1rem; background: linear-gradient(135deg, rgba(128,128,128,.045), rgba(128,128,128,.015)); }
        .assessment-hero::before { content: ""; position: absolute; inset: 0 auto 0 0; width: 4px; background: var(--det-color, #2563eb); }
        .assessment-hero-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
        .assessment-kicker { color: rgba(128,128,128,.95); font-size: .72rem; font-weight: 750; letter-spacing: .10em; text-transform: uppercase; }
        .assessment-title { margin-top: .18rem; font-size: 1.55rem; font-weight: 760; letter-spacing: -.025em; line-height: 1.2; }
        .assessment-status { display: inline-flex; align-items: center; gap: .42rem; padding: .42rem .78rem; border-radius: 999px; border: 1px solid transparent; font-size: .76rem; font-weight: 760; letter-spacing: .04em; white-space: nowrap; }
        .assessment-status::before { content: ""; width: .48rem; height: .48rem; border-radius: 50%; background: currentColor; }
        .assessment-status.normal { color: #15803d; background: rgba(21,128,61,.08); border-color: rgba(21,128,61,.20); }
        .assessment-status.attention { color: #b45309; background: rgba(180,83,9,.09); border-color: rgba(180,83,9,.22); }
        .assessment-status.critical { color: #b91c1c; background: rgba(185,28,28,.08); border-color: rgba(185,28,28,.20); }
        .assessment-status.neutral { color: #6b7280; background: rgba(107,114,128,.08); border-color: rgba(107,114,128,.18); }
        .assessment-subtitle { margin-top: .65rem; color: rgba(128,128,128,.95); font-size: .84rem; line-height: 1.45; }
        .results-kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .65rem; margin: .65rem 0 1rem 0; }
        .results-kpi { min-width: 0; padding: .72rem .85rem; border: 1px solid rgba(128,128,128,.18); border-radius: .75rem; background: rgba(128,128,128,.025); }
        .results-kpi-label { color: rgba(128,128,128,.90); font-size: .68rem; font-weight: 650; letter-spacing: .025em; text-transform: uppercase; }
        .results-kpi-value { margin-top: .18rem; font-size: 1.08rem; font-weight: 740; line-height: 1.2; }
        .results-kpi-value.risk { color: #b91c1c; }
        .results-kpi-value.warning { color: #b45309; }
        .results-kpi-value.good { color: #15803d; }
        .results-section-note { margin: -.25rem 0 .7rem 0; color: rgba(128,128,128,.9); font-size: .8rem; }
        @media (max-width: 760px) { .assessment-hero-top { flex-direction: column; } .results-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_results_header(result: Any) -> None:
    """Render the compact executive header without changing assessment logic."""
    report = getattr(result, "report", None)
    report_status = getattr(report, "assessment_status", None)
    status = str(getattr(report_status, "value", report_status or "Unknown"))
    rules = get_rule_results(result)
    triggered = sum(rule_status(rule) == "TRIGGERED" for rule in rules)
    not_evaluable = sum(rule_status(rule) == "NOT_EVALUABLE" for rule in rules)

    st.markdown(
        f"""
        <div class="assessment-hero">
            <div class="assessment-hero-top">
                <div><div class="assessment-kicker">Credit Risk Monitoring</div><div class="assessment-title">Executive Credit Assessment</div></div>
                <div class="assessment-status {_status_class(status)}">{status}</div>
            </div>
            <div class="assessment-subtitle">Deterministic Rule Engine decision with reporting used only for executive narrative.</div>
        </div>
        <div class="results-kpi-grid">
            <div class="results-kpi"><div class="results-kpi-label">Rules evaluated</div><div class="results-kpi-value">{len(rules)}</div></div>
            <div class="results-kpi"><div class="results-kpi-label">Triggered</div><div class="results-kpi-value {'risk' if triggered else 'good'}">{triggered}</div></div>
            <div class="results-kpi"><div class="results-kpi-label">Not evaluable</div><div class="results-kpi-value {'warning' if not_evaluable else 'good'}">{not_evaluable}</div></div>
            <div class="results-kpi"><div class="results-kpi-label">Decision source</div><div class="results-kpi-value">Rule Engine</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_results(result: Any, assessment_position: Any, selected_reporting_mode: str) -> None:
    if result is None:
        return

    _apply_results_styles()
    st.markdown('<div class="results-divider"></div>', unsafe_allow_html=True)
    render_results_header(result)

    credit_case = getattr(result, "credit_case", None)
    if credit_case is not None:
        render_decision_path(result)
        render_final_assessment(credit_case)

        with st.expander("Risk drivers", expanded=False):
            st.caption("Triggered indicators ranked by deterministic distance from their configured threshold.")
            render_risk_driver_overview(credit_case)

        with st.expander("Rule Engine evidence", expanded=False):
            st.caption("Complete rule-level evidence, coverage by macro-area, filters and individual rule detail.")
            render_risk_indicator_dashboard(result)

        render_executive_synthesis(result)

        case_without_final = replace(credit_case, final_assessment=None)
        case_result = type("CaseResult", (), {"credit_case": case_without_final})()
        with st.expander("Detailed macro-area analysis", expanded=False):
            st.caption("Context, evidence, findings and limitations for each assessment area.")
            render_credit_analysis_case(case_result)
    else:
        with st.expander("Rule Engine evidence", expanded=True):
            render_risk_indicator_dashboard(result)
