from typing import Any

import streamlit as st

from app.ui.components import (
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
    Resolve the badge kind and label for the Executive Report.

    The badge reflects the actual generator used for the report,
    including deterministic fallback.

    Icons are intentionally not included in the labels because
    they are rendered centrally by show_badge().
    """

    if selected_reporting_mode == "Deterministic":

        return (
            "det",
            "Deterministic",
        )

    if generator_used == "FALLBACK":

        return (
            "fallback",
            "Deterministic fallback",
        )

    if generator_used == "PRIMARY":

        if selected_reporting_mode == (
            "Gemini + Fallback"
        ):

            return (
                "ai",
                "AI-generated — Gemini",
            )

        if selected_reporting_mode == (
            "Ollama + Fallback"
        ):

            return (
                "ai",
                "AI-generated — Local LLM",
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

    The two provenance cards are intentionally rendered vertically
    rather than side-by-side. This improves readability on narrow
    screens and mobile devices, preventing the explanatory text
    from appearing too close to the Executive Report card.
    """

    st.subheader(
        "Provenance of This Assessment"
    )

    st.caption(
        "A quick summary of which layer produced each part "
        "of the output below."
    )

    # ========================================================
    # Assessment Status & Rule Findings
    # ========================================================

    with st.container(
        border=True
    ):

        st.markdown(
            """
            <div style="
                font-weight:650;
                margin-bottom:0.55rem;
                font-size:1rem;
            ">
                Assessment Status &amp; Rule Findings
            </div>
            """,
            unsafe_allow_html=True,
        )

        show_badge(
            "Deterministic — Rule Engine",
            "det",
        )

        st.markdown(
            """
            <div class="metric-description"
                 style="
                    margin-top:0.65rem;
                    margin-bottom:0.25rem;
                    line-height:1.55;
                 ">
                Assessment status, severity and findings are
                determined exclusively by the rule engine.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ========================================================
    # Visual Separation
    # ========================================================

    st.markdown(
        """
        <div style="height:0.9rem;"></div>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # Executive Report
    # ========================================================

    with st.container(
        border=True
    ):

        st.markdown(
            """
            <div style="
                font-weight:650;
                margin-bottom:0.55rem;
                font-size:1rem;
            ">
                Executive Report
            </div>
            """,
            unsafe_allow_html=True,
        )

        show_badge(
            report_badge_label,
            report_badge_kind,
        )

        st.markdown(
            """
            <div class="metric-description"
                 style="
                    margin-top:0.65rem;
                    margin-bottom:0.25rem;
                    line-height:1.55;
                 ">
                The Executive Report provides natural-language
                communication of the deterministic assessment.
                When an LLM is used, it has no decision authority.
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
                "Executive Report generated by the "
                "deterministic fallback generator"
            )

        elif generator_used == "PRIMARY":

            if selected_reporting_mode == (
                "Gemini + Fallback"
            ):

                st.success(
                    "✓ Gemini Reporting"
                )

                st.caption(
                    "Executive Report generated by Gemini"
                )

            elif selected_reporting_mode == (
                "Ollama + Fallback"
            ):

                st.success(
                    "✓ Local LLM Reporting"
                )

                st.caption(
                    "Executive Report generated by local LLM"
                )

            else:

                st.success(
                    "✓ Deterministic Reporting"
                )

                st.caption(
                    "Executive Report generated deterministically"
                )

        else:

            st.info(
                "Reporting"
            )

            st.caption(
                "Executive Report generator information "
                "is unavailable"
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

    st.markdown(
        "### System Architecture"
    )

    architecture_col1, architecture_col2 = (
        st.columns(2)
    )

    with architecture_col1:

        st.markdown(
            """
            <div class="section-card det">
                <div style="font-weight:650;">
                    Decision Layer
                </div>
            """,
            unsafe_allow_html=True,
        )

        show_badge(
            "Deterministic",
            "det",
        )

        st.markdown(
            """
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
            """
            <div class="section-card ai">
                <div style="font-weight:650;">
                    Reporting Layer
                </div>
            """,
            unsafe_allow_html=True,
        )

        show_badge(
            "AI-assisted, with fallback",
            "ai",
        )

        st.markdown(
            """
                <ul style="margin-top:0.6rem; padding-left:1.1rem;
                    font-size:0.86rem;">
                    <li>Structured assessment as input</li>
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


def render_report_source(
    generator_used: str | None,
    selected_reporting_mode: str,
) -> None:
    """
    Render the provenance of the Executive Report.

    The Executive Report can be generated either by an LLM
    or by the deterministic report generator.

    Rule findings, assessment status, severity and limitations
    remain deterministic in all cases.

    Icons are rendered exclusively by show_badge().
    """

    # ========================================================
    # LLM-generated Executive Report
    # ========================================================

    if generator_used == "PRIMARY":

        if selected_reporting_mode == (
            "Gemini + Fallback"
        ):

            show_badge(
                "AI-generated — Gemini",
                "ai",
            )

            st.caption(
                "The Executive Report was generated by Gemini "
                "using the structured deterministic assessment "
                "as input. The LLM has no decision authority."
            )

            return

        if selected_reporting_mode == (
            "Ollama + Fallback"
        ):

            show_badge(
                "AI-generated — Local LLM",
                "ai",
            )

            st.caption(
                "The Executive Report was generated by the "
                "local LLM using the structured deterministic "
                "assessment as input. The LLM has no decision "
                "authority."
            )

            return

    # ========================================================
    # Deterministic fallback
    # ========================================================

    if generator_used == "FALLBACK":

        show_badge(
            "Deterministic fallback",
            "fallback",
        )

        st.caption(
            "The primary LLM generator was unavailable or "
            "failed. The Executive Report was therefore "
            "generated by the predefined deterministic "
            "fallback generator."
        )

        return

    # ========================================================
    # Deterministic Executive Report
    # ========================================================

    show_badge(
        "Deterministic — Rule Engine",
        "det",
    )

    st.caption(
        "The Executive Report was generated by the predefined "
        "deterministic report generator using configured "
        "report templates and deterministic assessment results."
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

    The Executive Report is generated either by an LLM
    or by the deterministic report generator.

    Rule findings and limitations are always deterministic.
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

    # ========================================================
    # Reporting Agent
    # ========================================================

    st.markdown(
        "### Reporting Agent"
    )

    st.caption(
        "The Reporting Agent produces the Executive Report "
        "from the deterministic assessment results."
    )

    render_report_source(
        generator_used=generator_used,
        selected_reporting_mode=selected_reporting_mode,
    )

    # --------------------------------------------------------
    # Fallback diagnostic
    # --------------------------------------------------------

    if (
        generator_used == "FALLBACK"
        and generation_error
    ):

        with st.expander(
            "Technical information",
            expanded=False,
        ):

            st.caption(
                f"Primary generator error: "
                f"{generation_error}"
            )

    # ========================================================
    # Executive Report
    # ========================================================

    st.markdown(
        "### Executive Report"
    )

    with st.container(
        border=True
    ):

        st.markdown(
            result.report.executive_summary
        )

    # ========================================================
    # Report Findings
    # ========================================================

    if result.report.findings_by_category:

        st.markdown(
            "### Report Findings"
        )

        show_badge(
            "Deterministic — Rule Engine",
            "det",
        )

        st.caption(
            "These findings are sourced directly from the "
            "deterministic rule engine. They are not generated "
            "or modified by the LLM."
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

    # ========================================================
    # Report Limitations
    # ========================================================

    if result.report.limitations:

        st.markdown(
            "### Report Limitations"
        )

        show_badge(
            "Deterministic — Rule Engine",
            "det",
        )

        st.caption(
            "These limitations originate from the deterministic "
            "assessment logic and are not generated by the LLM."
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

    # ========================================================
    # Provenance
    # ========================================================

    render_provenance(
        report_badge_kind=report_badge_kind,
        report_badge_label=report_badge_label,
    )

    # ========================================================
    # Assessment Overview
    # ========================================================

    render_assessment_overview(
        result
    )

    # ========================================================
    # Assessed Position
    # ========================================================

    render_assessed_position(
        assessment_position
    )

    # ========================================================
    # Execution Trace
    # ========================================================

    render_execution_trace(
        generator_used=generator_used,
        selected_reporting_mode=(
            selected_reporting_mode
        ),
        configured_model=configured_model,
    )

    # ========================================================
    # Tabs
    # ========================================================

    report_icon = (
        "🤖"
        if report_badge_kind == "ai"
        else (
            "⚠️"
            if report_badge_kind == "fallback"
            else "🔒"
        )
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
            f"{report_icon} Executive Report",
        ]
    )

    # ========================================================
    # Overview
    # ========================================================

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

    # ========================================================
    # Rule Findings
    # ========================================================

    with findings_tab:

        render_findings_tab(
            result
        )

    # ========================================================
    # Analysis
    # ========================================================

    with analysis_tab:

        render_analysis_tab(
            result
        )

    # ========================================================
    # Executive Report
    # ========================================================

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