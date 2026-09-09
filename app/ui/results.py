from typing import Any

import pandas as pd
import streamlit as st

from app.ui.charts import render_decision_path, render_rule_assessment_summary
from app.ui.credit_position import display_position_table
from app.ui.report import render_report_tab


def get_llm_model_from_result(result: Any) -> str | None:
    """Return the configured LLM model when it is available in the workflow result."""
    return getattr(result, "llm_model", None)


def resolve_report_badge(
    selected_reporting_mode: str,
    generator_used: str | None,
    configured_model: str | None,
) -> tuple[str, str]:
    """Resolve the badge from the generator that actually produced the report."""
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


def render_result_hero(result: Any) -> None:
    """Render a compact entry point focused on the final assessment."""
    assessment = getattr(result, "assessment", None)
    status_obj = getattr(assessment, "status", None)
    status = str(getattr(status_obj, "value", status_obj or "Unknown"))
    rules = _rule_results(result)
    triggered = sum(_status(rule) == "TRIGGERED" for rule in rules)
    not_evaluable = sum(_status(rule) == "NOT_EVALUABLE" for rule in rules)

    st.markdown("## Credit Assessment")
    st.caption("Final assessment and Executive Report generated from the current credit position.")

    with st.container(border=True):
        columns = st.columns([1.4, 1, 1, 1])
        with columns[0]:
            st.caption("Assessment")
            st.markdown(f"## {status.replace('_', ' ').title()}")
        with columns[1]:
            st.metric("Rules triggered", triggered)
        with columns[2]:
            st.metric("Rules evaluated", len(rules) - not_evaluable)
        with columns[3]:
            st.metric("Not evaluable", not_evaluable)


def render_compact_risk_summary(result: Any) -> None:
    """Show only the evidence needed to understand why the assessment was reached."""
    rules = _rule_results(result)
    triggered = [rule for rule in rules if _status(rule) == "TRIGGERED"]

    st.markdown("## Why this assessment?")
    st.caption("The following deterministic rules are the evidence behind the final assessment.")

    status_counts = {
        "Triggered": sum(_status(rule) == "TRIGGERED" for rule in rules),
        "Not triggered": sum(_status(rule) == "NOT_TRIGGERED" for rule in rules),
        "Not evaluable": sum(_status(rule) == "NOT_EVALUABLE" for rule in rules),
    }

    left, right = st.columns([1, 2])
    with left:
        st.metric("Active risk drivers", len(triggered))
        if not triggered:
            st.success("No rules were triggered.")
        elif len(triggered) == 1:
            st.warning("1 rule is driving the assessment.")
        else:
            st.warning(f"{len(triggered)} rules are driving the assessment.")

    with right:
        chart_data = pd.DataFrame(
            {"Status": list(status_counts), "Rules": list(status_counts.values())}
        )
        st.bar_chart(chart_data, x="Status", y="Rules", horizontal=True, height=190)

    if not triggered:
        return

    severity_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    triggered = sorted(
        triggered,
        key=lambda rule: severity_rank.get(_severity(rule).upper(), 99),
    )

    rows = []
    for rule in triggered[:5]:
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

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if len(triggered) > 5:
        st.caption(f"Showing the 5 highest-priority drivers out of {len(triggered)} triggered rules.")


def render_supporting_details(
    result: Any,
    assessment_position: Any,
) -> None:
    """Keep audit and technical detail available without competing with the report."""
    with st.expander("Evidence & technical details", expanded=False):
        st.markdown("### Decision path")
        render_decision_path(result)

        st.markdown("### Rule evidence")
        render_rule_assessment_summary(result)

        st.markdown("### Credit data used")
        if assessment_position is not None:
            display_position_table(assessment_position)
        else:
            st.info("The assessed credit position is not available.")

        st.markdown("### Methodology")
        st.write(
            "The Rule Engine determines the assessment status, rule outcomes, severity and thresholds. "
            "The Reporting layer converts that structured result into the Executive Report. "
            "Gemini and Ollama can generate the narrative, but they do not determine the credit assessment."
        )

        metadata = getattr(result, "execution_metadata", None)
        if metadata is not None:
            st.markdown("### Execution")
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
    """Render a concise result journey with the Executive Report as the focal output."""
    if result is None:
        return

    st.divider()

    generator_used = getattr(result, "report_generator_used", None)
    configured_model = get_llm_model_from_result(result)
    report_badge_kind, report_badge_label = resolve_report_badge(
        selected_reporting_mode=selected_reporting_mode,
        generator_used=generator_used,
        configured_model=configured_model,
    )

    # 1. Final assessment
    render_result_hero(result)

    # 2. Final business output
    with st.container(border=True):
        render_report_tab(
            result=result,
            selected_reporting_mode=selected_reporting_mode,
            report_badge_kind=report_badge_kind,
            report_badge_label=report_badge_label,
            configured_model=configured_model,
        )

    # 3. Minimal explanation of the result
    render_compact_risk_summary(result)

    # 4. Everything technical is secondary
    render_supporting_details(result, assessment_position)
