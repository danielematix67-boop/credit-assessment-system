import sys
from dataclasses import MISSING, fields
from pathlib import Path
from types import UnionType
from typing import Any, get_args, get_origin, get_type_hints

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

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    .app-subtitle {
        color: #6b7280;
        font-size: 1rem;
        margin-top: -0.5rem;
        margin-bottom: 1.5rem;
    }

    .section-description {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }

    .workflow-step {
        padding: 1rem;
        border-radius: 0.65rem;
        border: 1px solid rgba(128, 128, 128, 0.22);
        min-height: 85px;
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
# CreditPosition Introspection
# ============================================================

def get_credit_position_fields():
    """
    Return the fields defined by the CreditPosition dataclass.

    CreditPosition is the source of truth for the input schema.
    No financial field names are hard-coded in the Streamlit app.
    """

    return fields(CreditPosition)


def get_credit_position_type_hints() -> dict[str, Any]:
    """
    Return resolved type annotations for CreditPosition.

    get_type_hints() is used instead of field.type because
    it resolves annotations such as:

        float | None

    correctly.
    """

    return get_type_hints(CreditPosition)


def get_field_default(field) -> Any:
    """
    Return the default defined by the dataclass.

    If the field has no explicit default, return None.
    """

    if field.default is not MISSING:
        return field.default

    if field.default_factory is not MISSING:
        return field.default_factory()

    return None


# ============================================================
# Type Introspection Helpers
# ============================================================

def unwrap_optional(field_type: Any) -> tuple[Any, bool]:
    """
    Resolve Optional / Union-with-None annotations.

    Examples:

        float
            -> (float, False)

        float | None
            -> (float, True)

        str | None
            -> (str, True)

    This makes the Streamlit layer compatible with the
    CreditPosition model.
    """

    origin = get_origin(field_type)
    args = get_args(field_type)

    # Python 3.10+ syntax:
    #
    # float | None
    #
    # produces types.UnionType.
    if origin is UnionType:

        non_none_types = [
            argument
            for argument in args
            if argument is not type(None)
        ]

        if len(non_none_types) == 1:
            return non_none_types[0], True

    # typing.Optional / typing.Union
    #
    # This is kept for compatibility with other annotations.
    if args and type(None) in args:

        non_none_types = [
            argument
            for argument in args
            if argument is not type(None)
        ]

        if len(non_none_types) == 1:
            return non_none_types[0], True

    return field_type, False


def is_numeric_type(field_type: Any) -> bool:
    """
    Return True when the resolved type is int or float.
    """

    resolved_type, _ = unwrap_optional(field_type)

    return resolved_type in {
        int,
        float,
    }


def get_resolved_field_type(field_type: Any) -> Any:
    """
    Return the actual underlying type.

    Example:

        float | None -> float
    """

    resolved_type, _ = unwrap_optional(field_type)

    return resolved_type


# ============================================================
# Field Presentation
# ============================================================

def format_field_label(field_name: str) -> str:
    """
    Convert a Python field name into a readable UI label.

    Examples:

        ebitda_margin
            -> EBITDA Margin

        pfn_to_ebitda
            -> PFN To EBITDA

        change_in_finished_goods_inventory
            -> Change In Finished Goods Inventory
    """

    special_terms = {
        "ebitda": "EBITDA",
        "pfn": "PFN",
        "id": "ID",
    }

    words = field_name.split("_")

    formatted_words = []

    for word in words:

        if word.lower() in special_terms:
            formatted_words.append(
                special_terms[word.lower()]
            )

        else:
            formatted_words.append(
                word.capitalize()
            )

    return " ".join(formatted_words)


def format_field_description(
    field_name: str,
) -> str:
    """
    Generate a generic description for a field.

    The function does not determine business logic.
    It only improves UI readability.
    """

    label = format_field_label(field_name)

    return f"Input value for {label}."


# ============================================================
# Streamlit Field Creation
# ============================================================

def create_optional_numeric_field(
    field_name: str,
    label: str,
    resolved_type: Any,
    default: Any,
) -> Any:
    """
    Create a numeric widget for fields declared as:

        int | None
        float | None

    The user can explicitly leave the value missing.

    Returning None is important because None has semantic
    meaning in the CreditPosition model: missing information.
    """

    provided_key = (
        f"credit_position_{field_name}_provided"
    )

    value_key = (
        f"credit_position_{field_name}_value"
    )

    default_is_provided = default is not None

    provided = st.checkbox(
        f"Provide {label}",
        value=default_is_provided,
        key=provided_key,
        help=(
            f"Enable this field to provide a value for "
            f"{label}. Disable it to represent missing data."
        ),
    )

    if not provided:
        return None

    if resolved_type is int:

        numeric_default = (
            int(default)
            if default is not None
            else 0
        )

        return st.number_input(
            label,
            value=numeric_default,
            step=1,
            key=value_key,
            help=format_field_description(
                field_name
            ),
        )

    if resolved_type is float:

        numeric_default = (
            float(default)
            if default is not None
            else 0.0
        )

        return st.number_input(
            label,
            value=numeric_default,
            step=0.01,
            format="%.4f",
            key=value_key,
            help=format_field_description(
                field_name
            ),
        )

    raise TypeError(
        f"Unsupported optional numeric type: "
        f"{field_name} -> {resolved_type}"
    )


def create_streamlit_field(
    field,
    field_type: Any,
) -> Any:
    """
    Dynamically create a Streamlit widget from a
    CreditPosition dataclass field.

    Supported types:

        str
        int
        float
        str | None
        int | None
        float | None

    No CreditPosition attribute name is hard-coded here.
    """

    field_name = field.name

    label = format_field_label(
        field_name
    )

    default = get_field_default(
        field
    )

    resolved_type, is_optional = (
        unwrap_optional(field_type)
    )

    # --------------------------------------------------------
    # Required string
    # --------------------------------------------------------

    if resolved_type is str and not is_optional:

        string_default = (
            ""
            if default is None
            else str(default)
        )

        return st.text_input(
            label,
            value=string_default,
            key=f"credit_position_{field_name}",
            help=format_field_description(
                field_name
            ),
        )

    # --------------------------------------------------------
    # Optional string
    # --------------------------------------------------------

    if resolved_type is str and is_optional:

        provided = st.checkbox(
            f"Provide {label}",
            value=default is not None,
            key=f"credit_position_{field_name}_provided",
            help=(
                f"Enable this field to provide a value "
                f"for {label}."
            ),
        )

        if not provided:
            return None

        return st.text_input(
            label,
            value="" if default is None else str(default),
            key=f"credit_position_{field_name}_value",
            help=format_field_description(
                field_name
            ),
        )

    # --------------------------------------------------------
    # Required integer
    # --------------------------------------------------------

    if resolved_type is int and not is_optional:

        numeric_default = (
            0
            if default is None
            else int(default)
        )

        return st.number_input(
            label,
            value=numeric_default,
            step=1,
            key=f"credit_position_{field_name}",
            help=format_field_description(
                field_name
            ),
        )

    # --------------------------------------------------------
    # Required float
    # --------------------------------------------------------

    if resolved_type is float and not is_optional:

        numeric_default = (
            0.0
            if default is None
            else float(default)
        )

        return st.number_input(
            label,
            value=numeric_default,
            step=0.01,
            format="%.4f",
            key=f"credit_position_{field_name}",
            help=format_field_description(
                field_name
            ),
        )

    # --------------------------------------------------------
    # Optional numeric
    # --------------------------------------------------------

    if (
        is_optional
        and resolved_type in {
            int,
            float,
        }
    ):

        return create_optional_numeric_field(
            field_name=field_name,
            label=label,
            resolved_type=resolved_type,
            default=default,
        )

    # --------------------------------------------------------
    # Unsupported
    # --------------------------------------------------------

    raise TypeError(
        f"Unsupported CreditPosition field type: "
        f"{field_name} -> {field_type}"
    )


# ============================================================
# Build CreditPosition from UI
# ============================================================

def build_credit_position_from_ui() -> dict[str, Any]:
    """
    Dynamically build the data required to instantiate
    CreditPosition.

    The dataclass itself defines the UI schema.

    Therefore, adding a field such as:

        new_indicator: float | None = None

    to CreditPosition automatically adds the corresponding
    Streamlit input.
    """

    model_fields = (
        get_credit_position_fields()
    )

    type_hints = (
        get_credit_position_type_hints()
    )

    position_data: dict[str, Any] = {}

    columns = st.columns(3)

    for index, field in enumerate(
        model_fields
    ):

        column = columns[
            index % len(columns)
        ]

        field_type = type_hints[
            field.name
        ]

        with column:

            position_data[field.name] = (
                create_streamlit_field(
                    field=field,
                    field_type=field_type,
                )
            )

    return position_data


# ============================================================
# Sidebar Configuration
# ============================================================

with st.sidebar:

    st.title(
        "System Configuration"
    )

    st.caption(
        "Configure the reporting layer used by "
        "the assessment workflow."
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

    st.subheader(
        "Architecture Guarantees"
    )

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
    """

    assessment_service = (
        create_default_assessment_service()
    )

    analysis_agent = AnalysisAgent()

    deterministic_report_generator = (
        DeterministicReportGenerator()
    )

    if reporting_mode == "LLM + Fallback":

        api_key = st.secrets[
            "GEMINI_API_KEY"
        ]

        llm_client = GeminiClient(
            api_key=api_key,
        )

        llm_report_generator = (
            LLMReportGenerator(
                llm_client=llm_client,
            )
        )

        reporting_agent = ReportingAgent(
            report_generator=llm_report_generator,
            fallback_generator=(
                deterministic_report_generator
            ),
        )

    else:

        reporting_agent = ReportingAgent(
            report_generator=(
                deterministic_report_generator
            ),
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
    """
    Execute the assessment workflow.
    """

    return workflow.run(position)


# ============================================================
# Header
# ============================================================

st.title(
    "Credit Assessment System"
)

st.markdown(
    """
    <div class="app-subtitle">
        Deterministic credit-quality assessment with
        controlled AI-assisted reporting.
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# ============================================================
# Workflow Architecture
# ============================================================

st.subheader(
    "Assessment Workflow"
)

st.caption(
    "End-to-end processing architecture."
)

workflow_cols = st.columns(5)

workflow_steps = [
    (
        "01",
        "Credit Data",
        "Input",
    ),
    (
        "02",
        "Rule Engine",
        "Deterministic",
    ),
    (
        "03",
        "Analysis Agent",
        "Interpretation",
    ),
    (
        "04",
        "Reporting Agent",
        "Controlled generation",
    ),
    (
        "05",
        "Assessment Report",
        "Output",
    ),
]

for column, (
    number,
    title,
    description,
) in zip(
    workflow_cols,
    workflow_steps,
):

    with column:

        st.markdown(
            f"""
            <div class="workflow-step">
                <div class="workflow-number">
                    {number}
                </div>
                <div class="workflow-title">
                    {title}
                </div>
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

st.subheader(
    "Credit Position"
)

st.caption(
    "The input form is generated dynamically from "
    "the CreditPosition dataclass."
)

st.info(
    "CreditPosition is the source of truth for the "
    "assessment input schema. Optional fields can be "
    "left unavailable by disabling their input."
)

position_data = (
    build_credit_position_from_ui()
)


# ============================================================
# Input Summary
# ============================================================

st.divider()

st.subheader(
    "Input Summary"
)

summary_col1, summary_col2, summary_col3 = (
    st.columns(3)
)

provided_fields = sum(
    value is not None
    for value in position_data.values()
)

missing_fields = (
    len(position_data)
    - provided_fields
)

with summary_col1:

    st.metric(
        "Model Fields",
        len(position_data),
    )

with summary_col2:

    st.metric(
        "Provided",
        provided_fields,
    )

with summary_col3:

    st.metric(
        "Missing",
        missing_fields,
    )


# ============================================================
# Assessment Configuration
# ============================================================

st.divider()

st.subheader(
    "Assessment Configuration"
)

configuration_col1, configuration_col2 = (
    st.columns(2)
)

with configuration_col1:

    st.caption(
        f"Reporting mode: **{reporting_mode}**"
    )

with configuration_col2:

    st.caption(
        f"CreditPosition fields detected: "
        f"**{len(position_data)}**"
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

    try:

        position = CreditPosition(
            **position_data
        )

    except TypeError as error:

        st.error(
            "Unable to construct CreditPosition."
        )

        st.exception(error)

        st.stop()

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

    with st.spinner(
        spinner_message
    ):

        try:

            result = run_assessment(
                workflow,
                position,
            )

        except Exception as error:

            st.error(
                "Assessment execution failed."
            )

            st.exception(error)

            st.stop()

    st.session_state[
        "assessment_result"
    ] = result

    st.session_state[
        "assessment_position"
    ] = position


# ============================================================
# Results
# ============================================================

result = st.session_state.get(
    "assessment_result"
)

assessment_position = (
    st.session_state.get(
        "assessment_position"
    )
)


if result is not None:

    st.divider()

    # ========================================================
    # Assessment Overview
    # ========================================================

    st.subheader(
        "Assessment Overview"
    )

    st.caption(
        "High-level outcome of the deterministic assessment."
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
            len(
                result.analysis.key_findings
            ),
        )

    with col3:

        st.metric(
            "Risk Factors",
            len(
                result.analysis.risk_factors
            ),
        )

    with col4:

        st.metric(
            "Limitations",
            len(
                result.analysis.limitations
            ),
        )


    # ========================================================
    # Assessed Position
    # ========================================================

    st.subheader(
        "Assessed Position"
    )

    if assessment_position is not None:

        position_dict = {
            field.name: getattr(
                assessment_position,
                field.name,
            )
            for field in fields(
                assessment_position
            )
        }

        st.dataframe(
            position_dict,
            use_container_width=True,
        )


    # ========================================================
    # Execution Trace
    # ========================================================

    st.subheader(
        "Execution Trace"
    )

    st.caption(
        "Traceability of the main processing stages."
    )

    trace_cols = st.columns(4)

    with trace_cols[0]:

        st.success(
            "✓ Credit Data"
        )

        st.caption(
            "Position received"
        )

    with trace_cols[1]:

        st.success(
            "✓ Rule Engine"
        )

        st.caption(
            "Deterministic assessment"
        )

    with trace_cols[2]:

        st.success(
            "✓ Analysis Agent"
        )

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

    (
        overview_tab,
        findings_tab,
        analysis_tab,
        report_tab,
    ) = st.tabs(
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

        st.markdown(
            """
            The assessment status is produced by the
            deterministic assessment service and is not
            generated by the LLM.
            """
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

            for finding in (
                result.analysis.key_findings
            ):

                with st.container(
                    border=True
                ):

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
                "No rule violations or key findings "
                "were identified."
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

        analysis_col1, analysis_col2 = (
            st.columns(2)
        )

        with analysis_col1:

            st.markdown(
                "#### Key Findings"
            )

            if result.analysis.key_findings:

                for finding in (
                    result.analysis.key_findings
                ):

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

                for risk in (
                    result.analysis.risk_factors
                ):

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

                for limitation in (
                    result.analysis.limitations
                ):

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

        # ----------------------------------------------------
        # Report Findings
        # ----------------------------------------------------

        if result.report.findings_by_category:

            st.markdown(
                "### Report Findings"
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

        # ----------------------------------------------------
        # Report Limitations
        # ----------------------------------------------------

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