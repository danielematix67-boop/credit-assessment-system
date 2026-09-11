"""Decision bridge visualization for the case-based Results page."""

from typing import Any

import streamlit as st

from app.ui.results.helpers import (
    escape_html,
    get_rule_results,
    get_rule_sections,
    rule_indicator,
    rule_severity,
    rule_status,
)


def render_decision_path(result: Any) -> None:
    """Visualise the deterministic path from rule signals to final assessment."""
    credit_case = getattr(result, "credit_case", None)
    sections = get_rule_sections(result)
    rule_results = get_rule_results(result)
    final_assessment = getattr(credit_case, "final_assessment", None)
    if credit_case is None or not sections or not rule_results or final_assessment is None:
        return

    triggered_rules = [
        rule_result
        for rule_result in rule_results
        if rule_status(rule_result) == "TRIGGERED"
    ]
    findings_count = sum(len(getattr(section, "findings", []) or []) for section in sections)
    final_status_obj = getattr(final_assessment, "status", None)
    final_status = str(getattr(final_status_obj, "value", final_status_obj or "Unknown"))

    st.subheader("Decision Path")
    st.caption(
        "The path below connects deterministic Rule Engine signals to the findings "
        "and macro-area outcomes already stored in the CreditAssessmentCase."
    )

    area_chips = "".join(
        f'<span class="decision-chip">{escape_html(getattr(section, "name", "—"))} · '
        f'{escape_html(getattr(getattr(section, "status", None), "value", "Unknown"))}</span>'
        for section in sections
    )
    signal_chips = "".join(
        f'<span class="decision-chip">{escape_html(getattr(rule, "rule_id", "—"))} · '
        f'{escape_html(rule_indicator(rule))} · {escape_html(rule_severity(rule))}</span>'
        for rule in triggered_rules
    )
    if not signal_chips:
        signal_chips = '<span class="decision-chip decision-chip-muted">No triggered rules</span>'

    st.markdown(
        """
        <style>
        .decision-flow {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .55rem;
            margin: .55rem 0 .85rem 0;
        }
        .decision-node {
            min-width: 0;
            padding: .95rem 1rem;
            border: 1px solid rgba(128,128,128,.20);
            border-radius: .85rem;
            background: rgba(128,128,128,.025);
        }
        .decision-node.det { border-color: rgba(37,99,235,.30); background: rgba(37,99,235,.055); }
        .decision-node.result { border-color: rgba(185,28,28,.25); background: rgba(185,28,28,.045); }
        .decision-node-kicker { color: rgba(128,128,128,.95); font-size: .68rem; font-weight: 750; letter-spacing: .09em; text-transform: uppercase; }
        .decision-node-title { margin-top: .2rem; font-size: .95rem; font-weight: 730; line-height: 1.25; }
        .decision-node-value { margin-top: .45rem; font-size: 1.35rem; font-weight: 780; line-height: 1.1; }
        .decision-node-description { margin-top: .35rem; color: rgba(128,128,128,.95); font-size: .74rem; line-height: 1.4; }
        .decision-evidence { display: flex; flex-wrap: wrap; gap: .3rem; margin-top: .6rem; }
        .decision-chip { display: inline-flex; align-items: center; gap: .25rem; padding: .22rem .48rem; border-radius: 999px; border: 1px solid rgba(185,28,28,.18); background: rgba(185,28,28,.065); font-size: .68rem; font-weight: 650; }
        .decision-chip-muted { border-color: rgba(128,128,128,.18); background: rgba(128,128,128,.045); }
        @media (max-width: 900px) { .decision-flow { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
        @media (max-width: 600px) { .decision-flow { grid-template-columns: 1fr; } }
        </style>
        """,
        unsafe_allow_html=True,
    )

    status_class = "result" if final_status.upper() == "CRITICAL" else "det"
    flow = f"""
        <div class="decision-flow">
            <div class="decision-node det">
                <div class="decision-node-kicker">01 · Risk signals</div>
                <div class="decision-node-title">Rule Engine</div>
                <div class="decision-node-value">{len(triggered_rules)} triggered</div>
                <div class="decision-node-description">Existing RuleResult outputs; no recalculation in the UI.</div>
                <div class="decision-evidence">{signal_chips}</div>
            </div>
            <div class="decision-node det">
                <div class="decision-node-kicker">02 · Findings</div>
                <div class="decision-node-title">Case Findings</div>
                <div class="decision-node-value">{findings_count}</div>
                <div class="decision-node-description">Findings stored by the deterministic case assessment.</div>
            </div>
            <div class="decision-node det">
                <div class="decision-node-kicker">03 · Macro-areas</div>
                <div class="decision-node-title">Assessment Sections</div>
                <div class="decision-node-value">{len(sections)}</div>
                <div class="decision-node-description">Section statuses are read directly from the case.</div>
                <div class="decision-evidence">{area_chips}</div>
            </div>
            <div class="decision-node {status_class}">
                <div class="decision-node-kicker">04 · Final assessment</div>
                <div class="decision-node-title">Case Decision</div>
                <div class="decision-node-value">{escape_html(final_status)}</div>
                <div class="decision-node-description">Final status returned by the deterministic assessment engine.</div>
            </div>
        </div>
    """
    st.markdown(flow, unsafe_allow_html=True)
    st.caption(
        "Explanatory view only: the Streamlit layer does not create a new risk score "
        "or modify RuleResult, findings, section status, or final assessment."
    )
