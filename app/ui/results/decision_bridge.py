"""Decision bridge visualization for the Results page."""

from typing import Any

import streamlit as st

from app.ui.results.helpers import (
    escape_html,
    get_rule_results,
    rule_indicator,
    rule_severity,
    rule_status,
    rule_status_counts,
)


def render_decision_path(result: Any) -> None:
    """Explain visually how deterministic rule outcomes lead to the assessment."""
    rule_results = get_rule_results(result)
    if not rule_results:
        return

    assessment = getattr(result, "assessment", None)
    status_obj = getattr(assessment, "status", None)
    assessment_status = str(
        getattr(status_obj, "value", str(status_obj or "Unknown"))
    )
    counts = rule_status_counts(result)
    triggered_rules = [
        rule_result
        for rule_result in rule_results
        if rule_status(rule_result) == "TRIGGERED"
    ]
    not_evaluable = counts["NOT_EVALUABLE"]

    st.subheader("How the Decision Is Produced")
    st.caption(
        "A transparent view of how the deterministic Rule Engine converts financial "
        "indicators into risk evidence and the final monitoring judgement."
    )

    st.markdown(
        """
        <style>
        .decision-flow {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 42px minmax(0, 1.25fr) 42px minmax(0, 1fr);
            align-items: stretch;
            gap: .45rem;
            margin: .55rem 0 .85rem 0;
        }
        .decision-node {
            min-width: 0;
            padding: 1rem 1.05rem;
            border: 1px solid rgba(128,128,128,.20);
            border-radius: .85rem;
            background: rgba(128,128,128,.025);
        }
        .decision-node.det {
            border-color: rgba(37,99,235,.30);
            background: rgba(37,99,235,.055);
        }
        .decision-node.result {
            border-color: rgba(185,28,28,.25);
            background: rgba(185,28,28,.045);
        }
        .decision-node-kicker {
            color: rgba(128,128,128,.95);
            font-size: .68rem;
            font-weight: 750;
            letter-spacing: .09em;
            text-transform: uppercase;
        }
        .decision-node-title {
            margin-top: .2rem;
            font-size: .98rem;
            font-weight: 730;
            line-height: 1.25;
        }
        .decision-node-value {
            margin-top: .45rem;
            font-size: 1.45rem;
            font-weight: 780;
            line-height: 1.1;
        }
        .decision-node-description {
            margin-top: .35rem;
            color: rgba(128,128,128,.95);
            font-size: .76rem;
            line-height: 1.4;
        }
        .decision-arrow {
            display: flex;
            align-items: center;
            justify-content: center;
            color: rgba(128,128,128,.85);
            font-size: 1.25rem;
            font-weight: 650;
        }
        .decision-evidence {
            display: flex;
            flex-wrap: wrap;
            gap: .35rem;
            margin-top: .65rem;
        }
        .decision-chip {
            display: inline-flex;
            align-items: center;
            gap: .3rem;
            padding: .24rem .52rem;
            border-radius: 999px;
            border: 1px solid rgba(185,28,28,.18);
            background: rgba(185,28,28,.065);
            font-size: .70rem;
            font-weight: 650;
        }
        .decision-chip-muted {
            border-color: rgba(128,128,128,.18);
            background: rgba(128,128,128,.045);
        }
        .decision-legend {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin: .15rem 0 .35rem 0;
            color: rgba(128,128,128,.95);
            font-size: .74rem;
        }
        @media (max-width: 760px) {
            .decision-flow {
                grid-template-columns: 1fr;
            }
            .decision-arrow {
                transform: rotate(90deg);
                min-height: 22px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    evidence_chips = "".join(
        f'<span class="decision-chip">{escape_html(getattr(rule, "rule_id", "—"))} · '
        f'{escape_html(rule_indicator(rule))} · {escape_html(rule_severity(rule))}</span>'
        for rule in triggered_rules
    )
    if not evidence_chips:
        evidence_chips = (
            '<span class="decision-chip decision-chip-muted">'
            "No triggered rules"
            "</span>"
        )

    status_class = "result" if assessment_status.upper() == "CRITICAL" else "det"
    decision_flow = f"""
        <div class="decision-flow">
            <div class="decision-node det">
                <div class="decision-node-kicker">01 · Inputs</div>
                <div class="decision-node-title">Financial Indicators</div>
                <div class="decision-node-value">{len(rule_results)}</div>
                <div class="decision-node-description">
                    Deterministic indicators evaluated from the credit position.
                </div>
            </div>
            <div class="decision-arrow">→</div>
            <div class="decision-node det">
                <div class="decision-node-kicker">02 · Evidence</div>
                <div class="decision-node-title">Rule Engine Outcomes</div>
                <div class="decision-node-value">{len(triggered_rules)} triggered</div>
                <div class="decision-node-description">
                    Triggered rules provide the factual risk evidence used by the assessment.
                </div>
                <div class="decision-evidence">{evidence_chips}</div>
            </div>
            <div class="decision-arrow">→</div>
            <div class="decision-node {status_class}">
                <div class="decision-node-kicker">03 · Judgement</div>
                <div class="decision-node-title">Monitoring Assessment</div>
                <div class="decision-node-value">{escape_html(assessment_status)}</div>
                <div class="decision-node-description">
                    Final status returned by the deterministic assessment engine.
                </div>
            </div>
        </div>
        <div class="decision-legend">
            <span>● Deterministic Rule Engine</span>
            <span>● Triggered rules = risk evidence</span>
            <span>● Not evaluable indicators: {not_evaluable}</span>
        </div>
    """
    st.markdown(decision_flow, unsafe_allow_html=True)

    st.caption(
        "The flow is explanatory only: it visualises existing RuleResult outputs and "
        "does not recalculate thresholds, severity or assessment status."
    )
