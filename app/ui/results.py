from typing import Any

import streamlit as st

from app.ui.components import (
    render_badge,
    show_badge,
)
from app.ui.credit_position import (
    display_position_table,
)


def get_llm_model_from_result(
    result: Any,
) -> str | None:
    """
    Retrieve the configured LLM model from the workflow result.
    """

    return getattr(
        result,
        "llm_model",
        None,
    )


def resolve_report_badge(
    selected_reporting_mode: str,
    generator_used: str | None,
    configured_model: str | None,
) -> tuple[str, str]:
    """
    Resolve the badge kind and label for the executive report.

    The badge reflects the actual generator used for the report,
    including deterministic fallback.
    """

    if selected_reporting_mode == "Deterministic":

        return (
            "det",
            "Deterministic",
        )

    if generator_used == "FALLBACK":

        return (
            "fallback",
            "Deterministic fallback "
            "(LLM unavailable)",
        )

    if generator_used == "PRIMARY":

        if selected_reporting_mode == (
            "Gemini + Fallback"
        ):

            return (
                "ai",
                "AI-generated (Gemini)",
            )

        if selected_reporting_mode == (
            "Ollama + Fallback"
        ):

            return (
                "ai",
                "AI-generated (Local LLM)",
            )

        return (
            "det",
            "Deterministic",
        )

    return (
        "fallback",
        "Unknown",
    )


def render_provenance(
    report_badge_kind: str,
    report_badge_label: str,
) -> None:
    """
    Render the provenance panel.
    """

    st.subheader(
        "Provenance of This Assessment"
    )

    st.caption(
        "A quick summary of which layer produced each part "
        "of the output below."
    )

    provenance_col1, provenance_col2 = (
        st.columns(2)
    )

    with provenance_col1:

        st.markdown(
            f"""
            <div class="section-card det">
                <div style="font-weight:650; margin-bottom:0.3rem;">
                    Assessment Status &amp; Rule Findings
                </div>
                {render_badge(
                    "Deterministic — Rule Engine",
                    "det"
                )}
                <div class="metric-description"
                     style="margin-top:0.5rem;">
                    Assessment status, severity and findings are
                    determined exclusively by the rule engine.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with provenance_col2:

        st.markdown(
            f"""
            <div class="section-card {report_badge_kind}">
                <div style="font-weight:650; margin-bottom:0.3rem;">
                    Executive Report
                </div>
                {render_badge(
                    report_badge_label,
                    report_badge_kind
                )}
                <div class="metric-description"
                     style="margin-top:0.5rem;">
                    Natural-language phrasing only — it cannot alter
                    the assessment status or deterministic findings.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_assessment_overview(
    result: Any,
) -> None:
    """
    Render the high-level assessment metrics.
    """

    st.subheader(
        "Assessment Overview"
    )

    st.caption(
        "High-level outcome of the deterministic assessment "
        "and execution of the reporting workflow."
    )

    # --------------------------------------------------------
    # Primary Metrics
    # --------------------------------------------------------

    primary_cols = st.columns(3)

    with primary_cols[0]:

        st.metric(
            "Assessment Status",
            result.assessment.status.value,
        )

    with primary_cols[1]:

        st.metric(
            "Key Findings",
            len(result.analysis.key_findings),
        )

    with primary_cols[2]:

        st.metric(
            "Risk Factors",
            len(result.analysis.risk_factors),
        )

    # --------------------------------------------------------
    # Execution Metrics
    # --------------------------------------------------------

    execution_cols = st.columns(3)

    with execution_cols[0]:

        st.metric(
            "Limitations",
            len(result.analysis.limitations),
        )

    with execution_cols[1]:

        st.metric(
            "Total Execution",
            f"{result.total_elapsed_time:.2f} s",
        )

    with execution_cols[2]:

        st.metric(
            "Reporting",
            f"{result.reporting_elapsed_time:.2f} s",
        )


def render_assessed_position(
    assessment_position: Any,
) -> None:
    """
    Render the credit position used by the assessment.
    """

    st.subheader(
        "Assessed Credit Position"
    )

    st.caption(
        "Financial inputs received by the assessment workflow. "
        "These values are displayed for traceability and are "
        "not generated or modified by the assessment engine."
    )

    if assessment_position is not None:

        display_position_table(
            assessment_position
        )


def render_execution_trace(
    generator_used: str | None,
    selected_reporting_mode: str,
    configured_model: str | None,
) -> None:
    """
    Render the execution trace of the assessment workflow.
    """

    st.subheader(
        "Execution Trace"
    )

    st.caption(
        "Traceability of the main processing stages."
    )

    # ========================================================
    # Row 1
    # ========================================================

    trace_row_1 = st.columns(2)

    with trace_row_1[0]:

        st.success(
            "✓ Credit Data"
        )

        st.caption(
            "Position received"
        )

    with trace_row_1[1]:

        st.success(
            "✓ Rule Engine"
        )

        st.caption(
            "Deterministic assessment"
        )

    # ========================================================
    # Row 2
    # ========================================================

    trace_row_2 = st.columns(2)

    with trace_row_2[0]:

        st.success(
            "✓ Analysis Agent"
        )

        st.caption(
            "Assessment interpreted"
        )

    with trace_row_2[1]:

        if generator_used == "FALLBACK":

            st.warning(
                "⚠ Reporting Fallback"
            )

            st.caption(
                "Deterministic fallback generator used"
            )

        elif generator_used == "PRIMARY":

            if selected_reporting_mode == (
                "Gemini + Fallback"
            ):

                st.success(
                    "✓ Gemini Reporting"
                )

                st.caption(
                    "AI-assisted report generated"
                )

            elif selected_reporting_mode == (
                "Ollama + Fallback"
            ):

                st.success(
                    "✓ Local LLM Reporting"
                )

                st.caption(
                    "AI-assisted report generated"
                )

            else:

                st.success(
                    "✓ Reporting"
                )

                st.caption(
                    "Deterministic report generated"
                )

        else:

            st.info(
                "Reporting"
            )

            st.caption(
                "Generator information unavailable"
            )


def render_overview_tab(
    result: Any,
    selected_reporting_mode: str,
    report_badge_kind: str,
    report_badge_label: str,
    configured_model: str | None,
) -> None:
    """
    Render the Overview tab.
    """

    st.markdown(
        "### Assessment Summary"
    )

    status = (
        result.assessment.status.value
    )

    normalized_status = (
        status.upper()
        .replace("-", "_")
    )

    if normalized_status in {
        "CRITICAL",
        "HIGH_RISK",
        "HIGH RISK",
    }:

        st.error(
            f"Assessment Status: **{status}**"
        )

    elif normalized_status in {
        "WARNING",
        "MEDIUM_RISK",
        "MEDIUM RISK",
    }:

        st.warning(
            f"Assessment Status: **{status}**"
        )

    else:

        st.success(
            f"Assessment Status: **{status}**"
        )

    show_badge(
        "Determined by rule engine only",
        "det",
    )

    st.markdown(
        """
        The assessment status is produced by the
        deterministic assessment service and is not
        generated by the LLM.
        """
    )

    st.markdown(
        "### Input Source"
    )

    input_source = st.session_state.get(
        "assessment_input_mode",
        "Unknown",
    )

    if input_source == "Demo Scenario":

        selected_scenario = (
            st.session_state.get(
                "assessment_scenario"
            )
        )

        st.info(
            f"Assessment executed using demo scenario: "
            f"**{selected_scenario}**"
        )

    else:

        st.info(
            "Assessment executed using manually "
            "provided credit data."
        )

    st.markdown(
        "### Reporting Configuration"
    )

    st.info(
        f"Reporting layer: "
        f"**{selected_reporting_mode}**"
    )

    show_badge(
        report_badge_label,
        report_badge_kind,
    )

    # Intentionally do not display the configured
    # LLM model or host in the user interface.

    st.markdown(
        "### System Architecture"
    )

    architecture_col1, architecture_col2 = (
        st.columns(2)
    )

    with architecture_col1:

        st.markdown(
            f"""
            <div class="section-card det">
                <div style="font-weight:650;">
                    Decision Layer
                </div>
                {render_badge("Deterministic", "det")}
                <ul style="margin-top:0.6rem; padding-left:1.1rem;
                    font-size:0.86rem;">
                    <li>Deterministic rule engine</li>
                    <li>Configured thresholds</li>
                    <li>Rule-based severity</li>
                    <li>Traceable findings</li>
                    <li>Deterministic assessment status</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with architecture_col2:

        st.markdown(
            f"""
            <div class="section-card ai">
                <div style="font-weight:650;">
                    Reporting Layer
                </div>
                {render_badge(
                    "AI-assisted, with fallback",
                    "ai"
                )}
                <ul style="margin-top:0.6rem; padding-left:1.1rem;
                    font-size:0.86rem;">
                    <li>Structured analysis as input</li>
                    <li>Optional LLM generation</li>
                    <li>Cloud or local LLM provider</li>
                    <li>No decision authority</li>
                    <li>Deterministic fallback</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_findings_tab(
    result: Any,
) -> None:
    """
    Render the deterministic rule findings tab.
    """

    st.markdown(
        "### Deterministic Rule Engine Findings"
    )

    show_badge(
        "Deterministic — fully traceable",
        "det",
    )

    st.caption(
        "These findings constitute the factual basis "
        "of the assessment. No LLM is involved in this tab."
    )

    if not result.analysis.key_findings:

        st.success(
            "No rule violations or key findings "
            "were identified."
        )

        return

    for finding in result.analysis.key_findings:

        with st.container(
            border=True
        ):

            finding_col1, finding_col2 = (
                st.columns(
                    [1.2, 4.8]
                )
            )

            with finding_col1:

                st.markdown(
                    f"**{finding.rule_id}**"
                )

                st.caption(
                    finding.severity.value
                )

            with finding_col2:

                st.markdown(
                    f"**{finding.category.upper()}**"
                )

                st.write(
                    finding.text
                )


def render_analysis_tab(
    result: Any,
) -> None:
    """
    Render the Analysis Agent tab.

    The Analysis Agent provides a structured interpretation
    of the deterministic assessment output.

    No LLM is involved in this layer.
    """

    st.markdown(
        "### Analysis Agent"
    )

    show_badge(
        "Deterministic — rule-based interpretation",
        "det",
    )

    st.caption(
        "Structured interpretation of the deterministic "
        "assessment output. No LLM is involved in this tab."
    )

    # ========================================================
    # Key Findings
    # ========================================================

    st.markdown(
        "#### Key Findings"
    )

    if result.analysis.key_findings:

        for finding in result.analysis.key_findings:

            with st.container(
                border=True
            ):

                finding_col1, finding_col2 = (
                    st.columns(
                        [1.2, 4.8]
                    )
                )

                with finding_col1:

                    st.markdown(
                        f"**{finding.rule_id}**"
                    )

                    st.caption(
                        finding.severity.value
                    )

                with finding_col2:

                    st.markdown(
                        f"**{finding.category.upper()}**"
                    )

                    st.write(
                        finding.text
                    )

    else:

        st.success(
            "No key findings were identified."
        )

    # ========================================================
    # Risk Factors
    # ========================================================

    st.markdown(
        "#### Risk Factors"
    )

    if result.analysis.risk_factors:

        for risk in result.analysis.risk_factors:

            with st.container(
                border=True
            ):

                st.markdown(
                    "**RISK FACTOR**"
                )

                st.write(
                    risk.text
                )

    else:

        st.success(
            "No risk factors were identified."
        )

    # ========================================================
    # Limitations
    # ========================================================

    st.markdown(
        "#### Limitations"
    )

    if result.analysis.limitations:

        for limitation in result.analysis.limitations:

            with st.container(
                border=True
            ):

                st.markdown(
                    "**LIMITATION**"
                )

                st.write(
                    limitation.text
                )

    else:

        st.success(
            "No limitations were identified."
        )


def render_report_tab(
    result: Any,
    selected_reporting_mode: str,
    report_badge_kind: str,
    report_badge_label: str,
    configured_model: str | None,
) -> None:
    """
    Render the Executive Report tab.
    """

    generator_used = getattr(
        result,
        "report_generator_used",
        None,
    )

    generation_error = getattr(
        result,
        "report_generation_error",
        None,
    )

    st.markdown(
        "### Reporting Agent"
    )

    show_badge(
        report_badge_label,
        report_badge_kind,
    )

    if generator_used == "FALLBACK":

        st.warning(
            "The primary report generator failed. "
            "The deterministic fallback generator was used."
        )

        if generation_error:

            st.caption(
                f"Technical reason: {generation_error}"
            )

    elif generator_used == "PRIMARY":

        if selected_reporting_mode == (
            "Gemini + Fallback"
        ):

            st.success(
                "Gemini generated the executive report "
                "successfully."
            )

            st.caption(
                "The LLM was used exclusively for report "
                "generation. The assessment outcome remains "
                "deterministic."
            )

        elif selected_reporting_mode == (
            "Ollama + Fallback"
        ):

            st.success(
                "Local LLM generated the executive report "
                "successfully."
            )

            st.caption(
                "The local LLM was used exclusively for "
                "report generation. The assessment outcome "
                "remains deterministic."
            )

        else:

            st.success(
                "Deterministic report generator completed "
                "successfully."
            )

    else:

        st.info(
            "Report generator information is unavailable."
        )

    st.markdown(
        "### Executive Report"
    )

    with st.container(
        border=True
    ):

        st.markdown(
            result.report.executive_summary
        )

    if result.report.findings_by_category:

        st.markdown(
            "### Report Findings"
        )

        show_badge(
            "Deterministic — sourced from rule engine",
            "det",
        )

        for group in (
            result.report.findings_by_category
        ):

            with st.expander(
                group.category.title(),
                expanded=True,
            ):

                for finding in (
                    group.findings
                ):

                    st.markdown(
                        f"**{finding.rule_id}** · "
                        f"{finding.severity.value}"
                    )

                    st.write(
                        finding.text
                    )

    if result.report.limitations:

        st.markdown(
            "### Report Limitations"
        )

        for limitation in (
            result.report.limitations
        ):

            st.warning(
                limitation.text
            )


def render_results(
    result: Any,
    assessment_position: Any,
    selected_reporting_mode: str,
) -> None:
    """
    Render the complete assessment result section.

    This function is intentionally responsible only for
    presentation. It does not execute assessment logic.
    """

    if result is None:

        return

    st.divider()

    generator_used = getattr(
        result,
        "report_generator_used",
        None,
    )

    configured_model = (
        get_llm_model_from_result(
            result
        )
    )

    report_badge_kind, report_badge_label = (
        resolve_report_badge(
            selected_reporting_mode=(
                selected_reporting_mode
            ),
            generator_used=generator_used,
            configured_model=configured_model,
        )
    )

    render_provenance(
        report_badge_kind=report_badge_kind,
        report_badge_label=report_badge_label,
    )

    render_assessment_overview(
        result
    )

    render_assessed_position(
        assessment_position
    )

    render_execution_trace(
        generator_used=generator_used,
        selected_reporting_mode=(
            selected_reporting_mode
        ),
        configured_model=configured_model,
    )

    (
        overview_tab,
        findings_tab,
        analysis_tab,
        report_tab,
    ) = st.tabs(
        [
            "Overview",
            "🔒 Rule Findings",
            "🔒 Analysis",
            (
                f"{'🤖' if report_badge_kind == 'ai' else ('⚠️' if report_badge_kind == 'fallback' else '🔒')} "
                "Executive Report"
            ),
        ]
    )

    with overview_tab:

        render_overview_tab(
            result=result,
            selected_reporting_mode=(
                selected_reporting_mode
            ),
            report_badge_kind=(
                report_badge_kind
            ),
            report_badge_label=(
                report_badge_label
            ),
            configured_model=configured_model,
        )

    with findings_tab:

        render_findings_tab(
            result
        )

    with analysis_tab:

        render_analysis_tab(
            result
        )

    with report_tab:

        render_report_tab(
            result=result,
            selected_reporting_mode=(
                selected_reporting_mode
            ),
            report_badge_kind=(
                report_badge_kind
            ),
            report_badge_label=(
                report_badge_label
            ),
            configured_model=configured_model,
        )