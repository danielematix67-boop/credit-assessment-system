import sys
from pathlib import Path

import streamlit as st


# ============================================================
# Project Path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Application Imports
# ============================================================

# ruff: noqa: E402

from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.llm_report_generator import (
    LLMReportGenerator,
)
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.llm.gemini_client import GeminiClient
from src.models.position import CreditPosition
from src.services.service_factory import create_default_assessment_service


# ============================================================
# Configuration
# ============================================================

st.set_page_config(
    page_title="Credit Assessment System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Styling
# ============================================================

st.markdown(
    """
    <style>

        /* --------------------------------------------------
           Global
        -------------------------------------------------- */

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }

        /* --------------------------------------------------
           Header
        -------------------------------------------------- */

        .app-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.2rem;
        }

        .app-title {
            font-size: 2.35rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin-bottom: 0;
        }

        .app-subtitle {
            color: #6b7280;
            font-size: 1.02rem;
            margin-top: 0.25rem;
            margin-bottom: 1.2rem;
        }

        .system-badge {
            display: inline-block;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            border: 1px solid rgba(128, 128, 128, 0.25);
            font-size: 0.82rem;
            font-weight: 600;
        }

        /* --------------------------------------------------
           Sections
        -------------------------------------------------- */

        .section-title {
            font-size: 1.35rem;
            font-weight: 650;
            margin-top: 1.2rem;
            margin-bottom: 0.2rem;
        }

        .section-description {
            color: #6b7280;
            font-size: 0.92rem;
            margin-bottom: 1rem;
        }

        /* --------------------------------------------------
           Workflow
        -------------------------------------------------- */

        .workflow-step {
            padding: 0.95rem 1rem;
            border-radius: 0.65rem;
            border: 1px solid rgba(128, 128, 128, 0.22);
            min-height: 78px;
            background: rgba(128, 128, 128, 0.025);
        }

        .workflow-number {
            font-size: 0.75rem;
            font-weight: 700;
            color: #6b7280;
            letter-spacing: 0.05em;
        }

        .workflow-title {
            font-weight: 650;
            margin-top: 0.2rem;
        }

        .workflow-description {
            color: #6b7280;
            font-size: 0.78rem;
        }

        /* --------------------------------------------------
           Cards
        -------------------------------------------------- */

        .info-card {
            padding: 1rem 1.1rem;
            border-radius: 0.7rem;
            border: 1px solid rgba(128, 128, 128, 0.22);
            background: rgba(128, 128, 128, 0.025);
        }

        .card-label {
            color: #6b7280;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .card-value {
            font-size: 1.35rem;
            font-weight: 700;
            margin-top: 0.2rem;
        }

        /* --------------------------------------------------
           Findings
        -------------------------------------------------- */

        .finding-card {
            padding: 0.85rem 1rem;
            border-radius: 0.6rem;
            border: 1px solid rgba(128, 128, 128, 0.20);
            margin-bottom: 0.55rem;
        }

        .finding-meta {
            color: #6b7280;
            font-size: 0.82rem;
        }

        /* --------------------------------------------------
           Sidebar
        -------------------------------------------------- */

        .sidebar-title {
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .sidebar-description {
            color: #6b7280;
            font-size: 0.85rem;
            margin-bottom: 1rem;
        }

        /* --------------------------------------------------
           Footer
        -------------------------------------------------- */

        .footer {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(128, 128, 128, 0.20);
            color: #6b7280;
            font-size: 0.78rem;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Sidebar Configuration
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-title">System Configuration</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-description">'
        "Configure the reporting layer used by the assessment workflow."
        "</div>",
        unsafe_allow_html=True,
    )

    reporting_mode = st.radio(
        "Reporting Mode",
        options=[
            "Deterministic",
            "LLM + Fallback",
        ],
        index=0,
    )

    st.divider()

    st.markdown("### Architecture Guarantees")

    st.markdown(
        """
        **Deterministic decision layer**
        
        The rule engine is the authoritative source
        of the assessment outcome.

        **Controlled AI usage**
        
        The LLM is restricted to report generation.

        **Traceability**
        
        Findings remain linked to deterministic rules.

        **Fallback**
        
        A deterministic report generator is retained
        if the LLM fails.
        """
    )

    st.divider()

    if reporting_mode == "LLM + Fallback":

        st.success(
            "AI reporting enabled"
        )

        st.caption(
            "Gemini is used exclusively for executive "
            "report generation."
        )

    else:

        st.info(
            "Deterministic reporting enabled"
        )

        st.caption(
            "No external LLM call is required."
        )


# ============================================================
# Workflow
# ============================================================


def create_workflow(
    reporting_mode: str,
) -> AssessmentWorkflow:
    """
    Build the assessment workflow.

    The deterministic rule engine remains the source of truth.
    The analysis and reporting layers consume its output.

    When LLM reporting is enabled, the LLM is used only for
    report generation. A deterministic generator is retained
    as a fallback in case of LLM failure.
    """

    assessment_service = create_default_assessment_service()

    analysis_agent = AnalysisAgent()

    deterministic_report_generator = (
        DeterministicReportGenerator()
    )

    if reporting_mode == "LLM + Fallback":

        api_key = st.secrets["GEMINI_API_KEY"]

        llm_client = GeminiClient(
            api_key=api_key,
        )

        llm_report_generator = LLMReportGenerator(
            llm_client=llm_client,
        )

        reporting_agent = ReportingAgent(
            report_generator=llm_report_generator,
            fallback_generator=deterministic_report_generator,
        )

    else:

        reporting_agent = ReportingAgent(
            report_generator=deterministic_report_generator,
        )

    return AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=analysis_agent,
        reporting_agent=reporting_agent,
    )


def run_assessment(
    workflow: AssessmentWorkflow,
    position: CreditPosition,
):
    return workflow.run(position)


# ============================================================
# Header
# ============================================================

st.markdown(
    """
    <div class="app-header">
        <div>
            <div class="app-title">
                Credit Assessment System
            </div>
            <div class="app-subtitle">
                Deterministic credit-quality assessment with
                controlled AI-assisted reporting.
            </div>
        </div>
        <div class="system-badge">
            SYSTEM ONLINE
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# ============================================================
# Workflow Architecture
# ============================================================

st.markdown(
    '<div class="section-title">Assessment Workflow</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-description">'
    "End-to-end processing architecture."
    "</div>",
    unsafe_allow_html=True,
)

workflow_cols = st.columns(5)

workflow_steps = [
    ("01", "Credit Data", "Input"),
    ("02", "Rule Engine", "Deterministic"),
    ("03", "Analysis Agent", "Interpretation"),
    ("04", "Reporting Agent", "Controlled generation"),
    ("05", "Assessment Report", "Output"),
]

for column, (number, title, description) in zip(
    workflow_cols,
    workflow_steps,
):

    with column:

        st.markdown(
            f"""
            <div class="workflow-step">
                <div class="workflow-number">{number}</div>
                <div class="workflow-title">{title}</div>
                <div class="workflow-description">
                    {description}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


st.divider()


# ============================================================
# Credit Position Input
# ============================================================

st.markdown(
    '<div class="section-title">Credit Position</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-description">'
    "Enter the financial indicators used by the deterministic "
    "assessment engine."
    "</div>",
    unsafe_allow_html=True,
)


col1, col2, col3 = st.columns(3)


# ------------------------------------------------------------
# Identification & Performance
# ------------------------------------------------------------

with col1:

    st.markdown("#### Company Information")

    position_id = st.text_input(
        "Position ID",
        value="DEMO_001",
    )

    revenue_growth = st.number_input(
        "Revenue Growth",
        value=-0.15,
        step=0.01,
        format="%.2f",
        help="Revenue growth rate.",
    )

    profit_loss = st.number_input(
        "Profit / Loss",
        value=-50000.0,
        step=5000.0,
        help="Profit or loss for the assessed period.",
    )


# ------------------------------------------------------------
# Profitability
# ------------------------------------------------------------

with col2:

    st.markdown("#### Profitability")

    ebitda = st.number_input(
        "EBITDA",
        value=-50000.0,
        step=5000.0,
        help="Earnings before interest, taxes, depreciation and amortization.",
    )

    ebitda_margin = st.number_input(
        "EBITDA Margin",
        value=-0.05,
        step=0.01,
        format="%.2f",
        help="EBITDA as a proportion of revenue.",
    )

    interest_expense = st.number_input(
        "Interest Expense",
        value=40000.0,
        step=5000.0,
        help="Interest expense used by profitability rules.",
    )


# ------------------------------------------------------------
# Leverage & Execution
# ------------------------------------------------------------

with col3:

    st.markdown("#### Leverage & Execution")

    pfn_to_ebitda = st.number_input(
        "PFN / EBITDA",
        value=6.0,
        step=0.5,
        help="Net financial position to EBITDA ratio.",
    )

    st.write("")

    st.markdown(
        "**Assessment configuration**"
    )

    st.caption(
        f"Reporting mode: **{reporting_mode}**"
    )

    run_button = st.button(
        "Run Assessment",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# Execute Workflow
# ============================================================

if run_button:

    position = CreditPosition(
        position_id=position_id,
        revenue_growth=revenue_growth,
        ebitda=ebitda,
        profit_loss=profit_loss,
        ebitda_margin=ebitda_margin,
        pfn_to_ebitda=pfn_to_ebitda,
        interest_expense=interest_expense,
    )

    workflow = create_workflow(
        reporting_mode=reporting_mode,
    )

    if reporting_mode == "LLM + Fallback":

        spinner_message = (
            "Executing deterministic assessment "
            "and generating AI-assisted report..."
        )

    else:

        spinner_message = (
            "Executing deterministic assessment workflow..."
        )

    with st.spinner(spinner_message):

        result = run_assessment(
            workflow,
            position,
        )

    st.session_state["assessment_result"] = result


# ============================================================
# Results
# ============================================================

result = st.session_state.get(
    "assessment_result",
)


if result is not None:

    st.divider()

    # ========================================================
    # Assessment Overview
    # ========================================================

    st.markdown(
        '<div class="section-title">Assessment Overview</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        "High-level outcome of the deterministic assessment."
        "</div>",
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Assessment Status",
            result.assessment.status.value,
        )


    with col2:

        st.metric(
            "Key Findings",
            len(result.analysis.key_findings),
        )


    with col3:

        st.metric(
            "Risk Factors",
            len(result.analysis.risk_factors),
        )


    with col4:

        st.metric(
            "Limitations",
            len(result.analysis.limitations),
        )


    # ========================================================
    # Execution Trace
    # ========================================================

    st.markdown(
        '<div class="section-title">Execution Trace</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        "Traceability of the main processing stages."
        "</div>",
        unsafe_allow_html=True,
    )

    trace_cols = st.columns(4)


    with trace_cols[0]:

        st.success("✓ Credit Data")

        st.caption(
            "Position received"
        )


    with trace_cols[1]:

        st.success("✓ Rule Engine")

        st.caption(
            "Deterministic assessment"
        )


    with trace_cols[2]:

        st.success("✓ Analysis Agent")

        st.caption(
            "Assessment interpreted"
        )


    with trace_cols[3]:

        generator_used = getattr(
            result,
            "report_generator_used",
            None,
        )

        if generator_used == "FALLBACK":

            st.warning(
                "⚠ Reporting Fallback"
            )

            st.caption(
                "Deterministic fallback generator used"
            )

        elif generator_used == "PRIMARY":

            if reporting_mode == "LLM + Fallback":

                st.success(
                    "✓ LLM Reporting"
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


    # ========================================================
    # Result Tabs
    # ========================================================

    overview_tab, findings_tab, analysis_tab, report_tab = st.tabs(
        [
            "Overview",
            "Rule Findings",
            "Analysis",
            "Executive Report",
        ]
    )


    # ========================================================
    # Overview Tab
    # ========================================================

    with overview_tab:

        st.markdown(
            "### Assessment Summary"
        )

        status = result.assessment.status.value

        if status.upper() in {
            "CRITICAL",
            "HIGH_RISK",
            "HIGH RISK",
        }:

            st.error(
                f"Assessment Status: **{status}**"
            )

        elif status.upper() in {
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

        st.markdown(
            "The assessment status is produced by the "
            "deterministic assessment service and is not "
            "generated by the LLM."
        )

        st.markdown("### System Architecture")

        architecture_col1, architecture_col2 = st.columns(2)

        with architecture_col1:

            st.markdown(
                """
                **Decision Layer**

                - Deterministic rule engine
                - Fixed thresholds
                - Rule-based severity
                - Traceable findings
                - Fixed assessment status
                """
            )

        with architecture_col2:

            st.markdown(
                """
                **Reporting Layer**

                - Structured analysis
                - Optional Gemini generation
                - No decision authority
                - Response validation
                - Deterministic fallback
                """
            )


    # ========================================================
    # Rule Findings Tab
    # ========================================================

    with findings_tab:

        st.markdown(
            "### Deterministic Rule Engine Findings"
        )

        st.caption(
            "These findings constitute the factual basis "
            "of the assessment."
        )

        if result.analysis.key_findings:

            for finding in result.analysis.key_findings:

                with st.container(border=True):

                    col1, col2 = st.columns(
                        [1.5, 5]
                    )

                    with col1:

                        st.markdown(
                            f"**{finding.rule_id}**"
                        )

                        st.caption(
                            finding.severity.value
                        )

                    with col2:

                        st.markdown(
                            f"**{finding.category.upper()}**"
                        )

                        st.write(
                            finding.text
                        )

        else:

            st.success(
                "No rule violations or key findings were identified."
            )


    # ========================================================
    # Analysis Tab
    # ========================================================

    with analysis_tab:

        st.markdown(
            "### Analysis Agent"
        )

        st.caption(
            "Structured interpretation of the deterministic "
            "assessment output."
        )

        analysis_col1, analysis_col2 = st.columns(2)


        with analysis_col1:

            st.markdown(
                "#### Key Findings"
            )

            if result.analysis.key_findings:

                for finding in result.analysis.key_findings:

                    st.write(
                        f"• {finding.text}"
                    )

            else:

                st.caption(
                    "No key findings."
                )


            st.markdown(
                "#### Risk Factors"
            )

            if result.analysis.risk_factors:

                for risk in result.analysis.risk_factors:

                    st.write(
                        f"• {risk.text}"
                    )

            else:

                st.caption(
                    "No risk factors."
                )


        with analysis_col2:

            st.markdown(
                "#### Limitations"
            )

            if result.analysis.limitations:

                for limitation in result.analysis.limitations:

                    st.write(
                        f"• {limitation.text}"
                    )

            else:

                st.caption(
                    "No limitations."
                )


    # ========================================================
    # Executive Report Tab
    # ========================================================

    with report_tab:

        st.markdown(
            "### Reporting Agent"
        )

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

            if reporting_mode == "LLM + Fallback":

                st.success(
                    "Gemini generated the executive report "
                    "successfully."
                )

                st.caption(
                    "The LLM was used exclusively for report "
                    "generation. The assessment outcome remains "
                    "deterministic."
                )

            else:

                st.success(
                    "Deterministic report generator completed successfully."
                )


        else:

            st.info(
                "Report generator information is unavailable."
            )


        st.markdown(
            "### Executive Report"
        )

        with st.container(border=True):

            st.markdown(
                result.report.executive_summary
            )


        # ----------------------------------------------------
        # Report Findings
        # ----------------------------------------------------

        if result.report.findings_by_category:

            st.markdown(
                "### Report Findings"
            )

            for group in result.report.findings_by_category:

                with st.expander(
                    group.category.title(),
                    expanded=True,
                ):

                    for finding in group.findings:

                        st.markdown(
                            f"**{finding.rule_id}** · "
                            f"{finding.severity.value}"
                        )

                        st.write(
                            finding.text
                        )


        # ----------------------------------------------------
        # Report Limitations
        # ----------------------------------------------------

        if result.report.limitations:

            st.markdown(
                "### Report Limitations"
            )

            for limitation in result.report.limitations:

                st.warning(
                    limitation.text
                )


# ============================================================
# Footer
# ============================================================

st.markdown(
    """
    <div class="footer">
        Credit Assessment System · Deterministic decision engine
        with controlled AI-assisted reporting.
        <br>
        The LLM does not determine assessment status,
        rule severity, thresholds, or credit decisions.
    </div>
    """,
    unsafe_allow_html=True,
)
