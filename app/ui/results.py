from typing import Any

import streamlit as st

from app.ui.charts import render_rule_assessment_summary
from app.ui.components import show_badge
from app.ui.credit_position import display_position_table
from app.ui.report import render_report_source, render_report_tab


def get_llm_model_from_result(result: Any) -> str | None:
    """Retrieve the configured LLM model from the workflow result."""
    return getattr(result, "llm_model", None)


def resolve_report_badge(
    selected_reporting_mode: str,
    generator_used: str | None,
    configured_model: str | None,
) -> tuple[str, str]:
    """Resolve the badge for the actual Executive Report generator."""
    if generator_used == "FALLBACK":
        return "fallback", "Deterministic fallback"

    if generator_used == "PRIMARY":
        if selected_reporting_mode == "Gemini + Fallback":
            return "ai", "AI-generated — Gemini"
        if selected_reporting_mode == "Ollama + Fallback":
            return "ai", "AI-generated — Local LLM"

    return "det", "Deterministic — Rule Engine"


def _normalized_status(result: Any) -> str:
    status = getattr(getattr(result, "assessment", None), "status", None)
    value = getattr(status, "value", str(status or "Unknown"))
    return str(value).upper().replace("-", "_")


def _status_kind(status: str) -> str:
    """Map assessment status to the existing badge categories."""
    if status in {"CRITICAL", "HIGH_RISK", "HIGH RISK"}:
        return "fallback"
    if status in {"WARNING", "MEDIUM_RISK", "MEDIUM RISK"}:
        return "fallback"
    return "det"


def _rule_status_counts(result: Any) -> dict[str, int]:
    """Count actual RuleResult statuses without applying business logic."""
    counts = {
        "TRIGGERED": 0,
        "NOT_TRIGGERED": 0,
        "NOT_EVALUABLE": 0,
    }

    assessment = getattr(result, "assessment", None)
    for rule_result in getattr(assessment, "rule_results", []) or []:
        status = getattr(getattr(rule_result, "status", None), "value", "")
        if status in counts:
            counts[status] += 1

    return counts


def render_result_hero(result: Any) -> None:
    """Render the primary result as the first thing the user sees."""
    status = getattr(
        getattr(getattr(result, "assessment", None), "status", None),
        "value",
        "Unknown",
    )
    status = str(status)
    status_kind = _status_kind(status.upper().replace("-", "_"))
    counts = _rule_status_counts(result)

    st.markdown("## Credit Assessment")
    st.caption(
        "The assessment result is determined by the deterministic Rule Engine. "
        "The AI layer is used only to produce the narrative report."
    )

    with st.container(border=True):
        result_col, metrics_col = st.columns([1.7, 3.3])

        with result_col:
            st.markdown("**ASSESSMENT RESULT**")
            show_badge(status, status_kind)
            st.markdown("### Why this result?")
            st.caption(
                "The sections below show the rule findings and quantitative "
                "evidence behind this outcome."
            )

        with metrics_col:
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.metric("Triggered", counts["TRIGGERED"])
            with metric_cols[1]:
                st.metric("Not triggered", counts["NOT_TRIGGERED"])
            with metric_cols[2]:
                st.metric("Not evaluable", counts["NOT_EVALUABLE"])


def render_why_section(result: Any) -> None:
    """Explain the main risk drivers using existing findings and rule results."""
    st.markdown("### Why? — Main Risk Drivers")
    st.caption(
        "Triggered rules are shown first because they are the rules whose conditions "
        "were met. Key findings are then shown as supporting evidence."
    )

    findings = list(
        getattr(getattr(result, "analysis", None), "key_findings", []) or []
    )
    rule_results = list(
        getattr(getattr(result, "assessment", None), "rule_results", []) or []
    )
    rule_by_id = {
        str(getattr(rule_result, "rule_id", "")): rule_result
        for rule_result in rule_results
    }

    if not findings:
        st.success("No key findings were identified by the assessment.")
        return

    enriched_findings = []
    for finding in findings:
        rule_id = str(getattr(finding, "rule_id", "—"))
        rule_result = rule_by_id.get(rule_id)
        status_obj = getattr(rule_result, "status", None) if rule_result else None
        rule_status = getattr(status_obj, "value", str(status_obj or "—"))
        enriched_findings.append(
            (rule_status == "TRIGGERED", finding, rule_result, rule_status)
        )

    enriched_findings.sort(key=lambda item: not item[0])
    triggered_count = sum(item[0] for item in enriched_findings)

    if triggered_count:
        st.warning(
            f"{triggered_count} key finding(s) are linked to triggered rules and "
            "should be read as the primary risk drivers."
        )

    supporting_started = False
    for is_triggered, finding, rule_result, rule_status in enriched_findings:
        if not is_triggered and not supporting_started:
            st.markdown("#### Supporting Findings")
            supporting_started = True

        rule_id = str(getattr(finding, "rule_id", "—"))
        severity_obj = getattr(finding, "severity", None)
        severity = getattr(severity_obj, "value", str(severity_obj or "—"))
        category = str(getattr(finding, "category", "—"))

        with st.container(border=True):
            if is_triggered:
                st.markdown("**PRIMARY RISK DRIVER**")
            else:
                st.markdown("**SUPPORTING FINDING**")

            header_cols = st.columns([1.4, 3.2, 1.4])

            with header_cols[0]:
                st.markdown(f"**{rule_id}**")
                st.caption("Rule")

            with header_cols[1]:
                st.markdown(f"**{category.upper()}**")
                st.caption("Category")

            with header_cols[2]:
                show_badge(str(severity), "fallback")
                st.caption("Severity")

            if rule_result is not None:
                indicator = str(getattr(rule_result, "rule_name", "—"))
                value = getattr(rule_result, "value", None)
                threshold = getattr(rule_result, "threshold", None)

                st.markdown(f"**Indicator:** {indicator}")

                evidence_cols = st.columns(3)
                with evidence_cols[0]:
                    st.metric("Rule status", str(rule_status))
                with evidence_cols[1]:
                    st.metric(
                        "Actual value",
                        "N/A" if value is None else f"{float(value):g}",
                    )
                with evidence_cols[2]:
                    st.metric(
                        "Threshold",
                        "N/A" if threshold is None else f"{float(threshold):g}",
                    )

            st.markdown("**Why it matters**")
            st.write(finding.text)


def render_assessment_evidence(result: Any) -> None:
    """Present the quantitative evidence supporting the assessment."""
    st.markdown("### Assessment Evidence")
    st.caption(
        "Use the rule summary to see the overall distribution, then select "
        "an individual rule to inspect its value, threshold and rationale."
    )
    render_rule_assessment_summary(result)


def render_assessed_position(assessment_position: Any) -> None:
    """Render the credit position used by the assessment."""
    st.markdown("### Credit Data Used")
    st.caption(
        "These are the financial inputs received by the assessment workflow. "
        "They are displayed for traceability and are not modified by the engine."
    )

    if assessment_position is not None:
        with st.expander("View assessed credit position", expanded=False):
            display_position_table(assessment_position)
    else:
        st.info("The assessed credit position is not available.")


def render_execution_trace(
    generator_used: str | None,
    selected_reporting_mode: str,
    configured_model: str | None,
) -> None:
    """Render a compact view of the assessment workflow."""
    st.markdown("### Assessment Workflow")
    st.caption("How the result is produced from input data to final report.")

    cols = st.columns(4)

    with cols[0]:
        st.success("✓ Credit Data")
        st.caption("Input position")

    with cols[1]:
        st.success("✓ Rule Engine")
        st.caption("Deterministic rules")

    with cols[2]:
        st.success("✓ Analysis")
        st.caption("Structured interpretation")

    with cols[3]:
        if generator_used == "FALLBACK":
            st.warning("⚠ Reporting")
            st.caption("Deterministic fallback")
        elif generator_used == "PRIMARY":
            if selected_reporting_mode == "Gemini + Fallback":
                st.success("✓ Reporting")
                st.caption("Gemini")
            elif selected_reporting_mode == "Ollama + Fallback":
                st.success("✓ Reporting")
                st.caption("Local LLM")
            else:
                st.success("✓ Reporting")
                st.caption("Deterministic")
        else:
            st.info("Reporting")
            st.caption("Generator unavailable")


def render_methodology(
    report_badge_kind: str,
    report_badge_label: str,
) -> None:
    """Explain the separation between decision and reporting layers."""
    with st.expander("How to read this assessment", expanded=False):
        st.markdown("**1. Decision Layer — Rule Engine**")
        show_badge("Deterministic", "det")
        st.write(
            "The assessment status, rule status, severity and thresholds "
            "come from the deterministic Rule Engine."
        )

        st.markdown("**2. Reporting Layer — Executive Report**")
        show_badge(report_badge_label, report_badge_kind)
        st.write(
            "The Reporting Layer turns the structured assessment into an "
            "executive narrative. It has no decision authority."
        )

        st.markdown("**How to interpret rule statuses**")
        st.write(
            "• **Triggered** — the rule condition was met.\n"
            "• **Not triggered** — the rule condition was not met.\n"
            "• **Not evaluable** — the required data was unavailable."
        )


def render_provenance(
    report_badge_kind: str,
    report_badge_label: str,
) -> None:
    """Render detailed provenance information."""
    st.subheader("Assessment Methodology")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Assessment Status & Rule Findings**")
        show_badge("Deterministic — Rule Engine", "det")
        st.caption(
            "Assessment status, severity and rule findings are determined "
            "exclusively by the deterministic rule engine."
        )
    with col2:
        st.markdown("**Executive Report**")
        show_badge(report_badge_label, report_badge_kind)
        st.caption(
            "The reporting layer interprets the structured assessment but "
            "has no decision authority."
        )


def render_assessment_overview(result: Any) -> None:
    """Render detailed assessment and execution metrics."""
    st.subheader("Assessment Overview")
    st.caption("Detailed outcome and workflow execution metrics.")

    cols = st.columns(6)
    values = [
        ("Status", result.assessment.status.value),
        ("Key Findings", len(result.analysis.key_findings)),
        ("Risk Factors", len(result.analysis.risk_factors)),
        ("Limitations", len(result.analysis.limitations)),
        ("Total Time", f"{result.total_elapsed_time:.2f} s"),
        ("Reporting", f"{result.reporting_elapsed_time:.2f} s"),
    ]

    for column, (label, value) in zip(cols, values):
        with column:
            st.metric(label, value)


def render_overview_tab(
    result: Any,
    selected_reporting_mode: str,
    report_badge_kind: str,
    report_badge_label: str,
    configured_model: str | None,
) -> None:
    """Render the detailed Overview tab."""
    render_provenance(report_badge_kind, report_badge_label)
    render_assessment_overview(result)

    st.markdown("### Input Source")
    input_source = st.session_state.get("assessment_input_mode", "Unknown")
    if input_source == "Demo Scenario":
        selected_scenario = st.session_state.get("assessment_scenario")
        st.info(f"Assessment executed using demo scenario: **{selected_scenario}**")
    else:
        st.info("Assessment executed using manually provided credit data.")

    st.markdown("### Reporting Configuration")
    st.info(f"Reporting layer: **{selected_reporting_mode}**")

    st.markdown("### System Architecture")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Decision Layer**")
        show_badge("Deterministic", "det")
        st.caption("Rule engine · thresholds · severity · traceable assessment status")

    with col2:
        st.markdown("**Reporting Layer**")
        show_badge("AI-assisted, with fallback", "ai")
        st.caption(
            "Structured assessment · optional LLM · deterministic fallback · no decision authority"
        )


def render_findings_tab(result: Any) -> None:
    """Render the deterministic rule findings tab."""
    st.markdown("### Rule Findings")
    show_badge("Deterministic — fully traceable", "det")
    st.caption("The factual rule findings that form the basis of the assessment.")

    findings = list(
        getattr(getattr(result, "analysis", None), "key_findings", []) or []
    )
    if not findings:
        st.success("No rule violations or key findings were identified.")
        return

    for finding in findings:
        with st.expander(
            f"{finding.rule_id} · {finding.category} · {finding.severity.value}",
            expanded=False,
        ):
            st.write(finding.text)


def render_analysis_tab(result: Any) -> None:
    """Render the structured analysis tab."""
    st.markdown("### Analysis")
    show_badge("Deterministic — rule-based interpretation", "det")
    st.caption("Structured interpretation of the deterministic assessment output.")

    sections = [
        (
            "Key Findings",
            result.analysis.key_findings,
            "No key findings were identified.",
        ),
        (
            "Risk Factors",
            result.analysis.risk_factors,
            "No risk factors were identified.",
        ),
        ("Limitations", result.analysis.limitations, "No limitations were identified."),
    ]

    for title, items, empty_message in sections:
        st.markdown(f"#### {title}")
        if not items:
            st.success(empty_message)
            continue

        for item in items:
            with st.container(border=True):
                if hasattr(item, "rule_id"):
                    st.markdown(f"**{item.rule_id}** · {item.severity.value}")
                else:
                    st.markdown(
                        f"**{title[:-1].upper() if title.endswith('s') else title.upper()}**"
                    )
                st.write(item.text)


def render_results(
    result: Any,
    assessment_position: Any,
    selected_reporting_mode: str,
) -> None:
    """Render the complete assessment result section."""
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

    # ========================================================
    # Primary user journey: RESULT -> WHY -> EVIDENCE -> DATA
    # ========================================================
    render_result_hero(result)
    render_why_section(result)
    render_assessment_evidence(result)
    render_assessed_position(assessment_position)
    render_execution_trace(
        generator_used=generator_used,
        selected_reporting_mode=selected_reporting_mode,
        configured_model=configured_model,
    )
    render_methodology(report_badge_kind, report_badge_label)

    st.markdown("---")
    st.markdown("### Detailed Results")
    st.caption("Open a section below when you need additional detail or traceability.")

    report_icon = (
        "🤖"
        if report_badge_kind == "ai"
        else "⚠️"
        if report_badge_kind == "fallback"
        else "🔒"
    )

    overview_tab, findings_tab, analysis_tab, report_tab = st.tabs(
        [
            "Overview",
            "🔒 Rule Findings",
            "🔒 Analysis",
            f"{report_icon} Executive Report",
        ]
    )

    with overview_tab:
        render_overview_tab(
            result=result,
            selected_reporting_mode=selected_reporting_mode,
            report_badge_kind=report_badge_kind,
            report_badge_label=report_badge_label,
            configured_model=configured_model,
        )

    with findings_tab:
        render_findings_tab(result)

    with analysis_tab:
        render_analysis_tab(result)

    with report_tab:
        render_report_tab(
            result=result,
            selected_reporting_mode=selected_reporting_mode,
            report_badge_kind=report_badge_kind,
            report_badge_label=report_badge_label,
            configured_model=configured_model,
        )
