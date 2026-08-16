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
)


# ============================================================
# Sidebar Configuration
# ============================================================

with st.sidebar:

    st.markdown("## System Configuration")

    reporting_mode = st.radio(
        "Reporting Mode",
        options=[
            "Deterministic",
            "LLM + Fallback",
        ],
        index=0,
    )

    st.divider()

    st.markdown("### System Guarantees")

    st.markdown(
        """
        ✓ Deterministic rule engine  
        ✓ Traceable findings  
        ✓ Fixed assessment status  
        ✓ LLM cannot modify rules  
        ✓ Automatic fallback
        """
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

        llm_client = GeminiClient()

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
# Styling
# ============================================================

st.markdown(
    """
    <style>

        .main-title {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            color: #6b7280;
            font-size: 1.05rem;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 650;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
        }

        .workflow-step {
            padding: 0.9rem 1rem;
            border-radius: 0.6rem;
            border: 1px solid rgba(128, 128, 128, 0.25);
            margin-bottom: 0.5rem;
            min-height: 75px;
        }

        .muted {
            color: #6b7280;
        }

        .trace-item {
            padding: 0.7rem 1rem;
            border-radius: 0.5rem;
            border: 1px solid rgba(128, 128, 128, 0.20);
            margin-bottom: 0.4rem;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Header
# ============================================================

st.markdown(
    '<div class="main-title">Credit Assessment System</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        Deterministic credit-quality assessment with
        structured analysis and controlled report generation.
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

workflow_cols = st.columns(5)

workflow_steps = [
    ("01", "Credit Data", "Input"),
    ("02", "Rule Engine", "Deterministic"),
    ("03", "Analysis Agent", "Interpretation"),
    ("04", "Reporting Agent", "Report generation"),
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
                <strong>{number} · {title}</strong><br>
                <span class="muted">{description}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()


# ============================================================
# Input
# ============================================================

st.markdown(
    '<div class="section-title">Credit Position</div>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)


with col1:

    position_id = st.text_input(
        "Position ID",
        value="DEMO_001",
    )

    revenue_growth = st.number_input(
        "Revenue Growth",
        value=-0.15,
        step=0.01,
        format="%.2f",
    )

    ebitda = st.number_input(
        "EBITDA",
        value=-50000.0,
        step=5000.0,
    )


with col2:

    profit_loss = st.number_input(
        "Profit / Loss",
        value=-50000.0,
        step=5000.0,
    )

    ebitda_margin = st.number_input(
        "EBITDA Margin",
        value=-0.05,
        step=0.01,
        format="%.2f",
    )

    pfn_to_ebitda = st.number_input(
        "PFN / EBITDA",
        value=6.0,
        step=0.5,
    )


with col3:

    interest_expense = st.number_input(
        "Interest Expense",
        value=40000.0,
        step=5000.0,
    )

    st.write("")
    st.write("")

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
            "Executing assessment and generating "
            "AI-assisted report..."
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
        '<div class="section-title">Assessment Result</div>',
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

    st.divider()

    st.markdown(
        '<div class="section-title">Execution Trace</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Trace of the main processing stages executed by the system."
    )

    trace_cols = st.columns(4)

    with trace_cols[0]:
        st.success("✓ Credit Data")
        st.caption("Position received")

    with trace_cols[1]:
        st.success("✓ Rule Engine")
        st.caption("Deterministic assessment")

    with trace_cols[2]:
        st.success("✓ Analysis Agent")
        st.caption("Assessment interpreted")

    with trace_cols[3]:

        generator_used = getattr(
            result,
            "report_generator_used",
            None,
        )

        if generator_used == "FALLBACK":

            st.warning("⚠ Reporting Fallback")

            st.caption(
                "Deterministic fallback generator used"
            )

        elif generator_used == "PRIMARY":

            if reporting_mode == "LLM + Fallback":

                st.success("✓ LLM Reporting")

                st.caption(
                    "LLM report generated successfully"
                )

            else:

                st.success("✓ Reporting")

                st.caption(
                    "Deterministic report generated"
                )

        else:

            st.info("Reporting")

            st.caption(
                "Generator information unavailable"
            )


    # ========================================================
    # Rule Engine
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">Rule Engine Findings</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "These findings originate from the deterministic "
        "assessment logic and represent the factual basis "
        "of the subsequent analysis."
    )

    if result.analysis.key_findings:

        for finding in result.analysis.key_findings:

            with st.container(border=True):

                col1, col2, col3 = st.columns(
                    [1.2, 1.5, 5]
                )

                with col1:
                    st.write(
                        f"**{finding.rule_id}**"
                    )

                with col2:
                    st.write(
                        f"**{finding.severity.value}**"
                    )

                with col3:

                    st.write(
                        f"**{finding.category.upper()}**"
                    )

                    st.write(
                        finding.text
                    )

    else:

        st.info(
            "The rule engine did not identify any key findings."
        )


    # ========================================================
    # Analysis Agent
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">Analysis Agent</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "The Analysis Agent interprets the structured output "
        "of the deterministic assessment engine."
    )

    analysis_col1, analysis_col2 = st.columns(2)

    with analysis_col1:

        st.markdown("#### Key Findings")

        if result.analysis.key_findings:

            for finding in result.analysis.key_findings:

                st.write(
                    f"• {finding.text}"
                )

        else:

            st.caption(
                "No key findings."
            )

        st.markdown("#### Risk Factors")

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

        st.markdown("#### Limitations")

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
    # Reporting Agent
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">Reporting Agent</div>',
        unsafe_allow_html=True,
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
                f"Reason: {generation_error}"
            )

    elif generator_used == "PRIMARY":

        if reporting_mode == "LLM + Fallback":

            st.success(
                "LLM report generator completed successfully."
            )

        else:

            st.success(
                "Deterministic report generator completed successfully."
            )

    else:

        st.info(
            "Report generator information is unavailable."
        )


    # ========================================================
    # Executive Report
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">Executive Report</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):

        st.markdown(
            result.report.executive_summary
        )


    # ========================================================
    # Report Findings
    # ========================================================

    if result.report.findings_by_category:

        st.divider()

        st.markdown(
            '<div class="section-title">Report Findings</div>',
            unsafe_allow_html=True,
        )

        for group in result.report.findings_by_category:

            with st.expander(
                group.category.title(),
                expanded=True,
            ):

                for finding in group.findings:

                    st.write(
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

        st.divider()

        st.markdown(
            '<div class="section-title">Report Limitations</div>',
            unsafe_allow_html=True,
        )

        for limitation in result.report.limitations:

            st.warning(
                limitation.text
            )