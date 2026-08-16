import sys
from dataclasses import MISSING, fields
from pathlib import Path
from types import UnionType
from typing import Any, get_args, get_origin, get_type_hints

import streamlit as st


# ============================================================
# Project Paths
# ============================================================

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


# ============================================================
# Application Imports
# ============================================================

# ruff: noqa: E402

from demo_scenarios import DEMO_SCENARIOS

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

    .scenario-card {
        padding: 1rem 1.2rem;
        border-radius: 0.65rem;
        border: 1px solid rgba(128, 128, 128, 0.22);
        background: rgba(128, 128, 128, 0.025);
        margin-bottom: 1rem;
    }

    .scenario-title {
        font-size: 1.05rem;
        font-weight: 650;
        margin-bottom: 0.3rem;
    }

    .scenario-description {
        color: #6b7280;
        font-size: 0.88rem;
    }

    .input-source-badge {
        display: inline-block;
        padding: 0.25rem 0.55rem;
        border-radius: 0.4rem;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(128, 128, 128, 0.25);
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

    CreditPosition remains the source of truth for the input
    schema.
    """

    return fields(CreditPosition)


def get_credit_position_type_hints() -> dict[str, Any]:
    """
    Return resolved type annotations for CreditPosition.
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
    """

    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is UnionType:

        non_none_types = [
            argument
            for argument in args
            if argument is not type(None)
        ]

        if len(non_none_types) == 1:
            return non_none_types[0], True

    if args and type(None) in args:

        non_none_types = [
            argument
            for argument in args
            if argument is not type(None)
        ]

        if len(non_none_types) == 1:
            return non_none_types[0], True

    return field_type, False


# ============================================================
# Field Presentation
# ============================================================

def format_field_label(field_name: str) -> str:
    """
    Convert a Python field name into a readable UI label.
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
    Generate a generic UI description.
    """

    label = format_field_label(field_name)

    return f"Input value for {label}."


# ============================================================
# Demo Scenario Builder
# ============================================================

def build_demo_position(
    scenario_name: str,
) -> CreditPosition:
    """
    Build a CreditPosition from a predefined demo scenario.

    Demo scenarios only provide input data.

    They do NOT contain assessment logic, rule outcomes,
    severity decisions or assessment status.

    The resulting CreditPosition is processed by the exact
    same AssessmentWorkflow used for manual input.
    """

    if scenario_name not in DEMO_SCENARIOS:
        raise ValueError(
            f"Unknown demo scenario: {scenario_name}"
        )

    scenario_values = DEMO_SCENARIOS[
        scenario_name
    ]["values"]

    type_hints = (
        get_credit_position_type_hints()
    )

    position_data: dict[str, Any] = {}

    for field in get_credit_position_fields():

        field_name = field.name

        # ----------------------------------------------------
        # Explicit scenario value
        # ----------------------------------------------------

        if field_name in scenario_values:

            position_data[field_name] = (
                scenario_values[field_name]
            )

            continue

        # ----------------------------------------------------
        # Dataclass default
        # ----------------------------------------------------

        default = get_field_default(field)

        if default is not None:

            position_data[field_name] = default

            continue

        # ----------------------------------------------------
        # No default: infer a safe demo value from the type.
        # ----------------------------------------------------

        field_type = type_hints[field_name]

        resolved_type, is_optional = (
            unwrap_optional(field_type)
        )

        if is_optional:

            position_data[field_name] = None

        elif resolved_type is str:

            position_data[field_name] = (
                f"DEMO-{field_name.upper()}"
            )

        elif resolved_type is int:

            position_data[field_name] = 0

        elif resolved_type is float:

            position_data[field_name] = 0.0

        else:

            raise TypeError(
                "Unable to create demo value for "
                f"{field_name}: {field_type}"
            )

    return CreditPosition(
        **position_data
    )


# ============================================================
# Manual Input
# ============================================================

def create_optional_numeric_field(
    field_name: str,
    label: str,
    resolved_type: Any,
    default: Any,
) -> Any:

    provided_key = (
        f"credit_position_{field_name}_provided"
    )

    value_key = (
        f"credit_position_{field_name}_value"
    )

    provided = st.checkbox(
        f"Provide {label}",
        value=default is not None,
        key=provided_key,
    )

    if not provided:
        return None

    if resolved_type is int:

        return st.number_input(
            label,
            value=(
                int(default)
                if default is not None
                else 0
            ),
            step=1,
            key=value_key,
        )

    if resolved_type is float:

        return st.number_input(
            label,
            value=(
                float(default)
                if default is not None
                else 0.0
            ),
            step=0.01,
            format="%.4f",
            key=value_key,
        )

    raise TypeError(
        f"Unsupported optional numeric type: "
        f"{field_name} -> {resolved_type}"
    )


def create_streamlit_field(
    field,
    field_type: Any,
) -> Any:

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

    if resolved_type is str and not is_optional:

        return st.text_input(
            label,
            value=(
                ""
                if default is None
                else str(default)
            ),
            key=f"credit_position_{field_name}",
        )

    if resolved_type is str and is_optional:

        provided = st.checkbox(
            f"Provide {label}",
            value=default is not None,
            key=f"credit_position_{field_name}_provided",
        )

        if not provided:
            return None

        return st.text_input(
            label,
            value=(
                ""
                if default is None
                else str(default)
            ),
            key=f"credit_position_{field_name}_value",
        )

    if resolved_type is int and not is_optional:

        return st.number_input(
            label,
            value=(
                0
                if default is None
                else int(default)
            ),
            step=1,
            key=f"credit_position_{field_name}",
        )

    if resolved_type is float and not is_optional:

        return st.number_input(
            label,
            value=(
                0.0
                if default is None
                else float(default)
            ),
            step=0.01,
            format="%.4f",
            key=f"credit_position_{field_name}",
        )

    if (
        is_optional
        and resolved_type in {int, float}
    ):

        return create_optional_numeric_field(
            field_name=field_name,
            label=label,
            resolved_type=resolved_type,
            default=default,
        )

    raise TypeError(
        f"Unsupported CreditPosition field type: "
        f"{field_name} -> {field_type}"
    )


def build_credit_position_from_ui() -> dict[str, Any]:

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

        with columns[
            index % len(columns)
        ]:

            position_data[field.name] = (
                create_streamlit_field(
                    field=field,
                    field_type=type_hints[
                        field.name
                    ],
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
    ("01", "Credit Data", "Input"),
    ("02", "Rule Engine", "Deterministic"),
    ("03", "Analysis Agent", "Interpretation"),
    ("04", "Reporting Agent", "Controlled generation"),
    ("05", "Assessment Report", "Output"),
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
# Credit Data Source
# ============================================================

st.subheader(
    "Credit Data"
)

st.caption(
    "Select a predefined scenario for the demonstration "
    "or switch to manual input for custom testing."
)

input_mode = st.radio(
    "Input Mode",
    options=[
        "Demo Scenario",
        "Manual Input",
    ],
    horizontal=True,
    label_visibility="collapsed",
)


# ============================================================
# Demo Scenario Input
# ============================================================

position: CreditPosition | None = None
position_data: dict[str, Any] | None = None

if input_mode == "Demo Scenario":

    scenario_name = st.selectbox(
        "Demo Scenario",
        options=list(
            DEMO_SCENARIOS.keys()
        ),
        index=0,
    )

    scenario = DEMO_SCENARIOS[
        scenario_name
    ]

    st.markdown(
        f"""
        <div class="scenario-card">
            <div class="scenario-title">
                {scenario_name}
            </div>
            <div class="scenario-description">
                {scenario["description"]}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:

        position = build_demo_position(
            scenario_name
        )

    except Exception as error:

        st.error(
            "Unable to construct the selected demo scenario."
        )

        st.exception(error)

        st.stop()

    st.markdown(
        "#### Scenario Data"
    )

    st.caption(
        "These values are input data only. "
        "The assessment is still performed entirely "
        "by the deterministic workflow."
    )

    scenario_dict = {
        field.name: getattr(
            position,
            field.name,
        )
        for field in fields(position)
    }

    display_data = {
        format_field_label(
            key
        ): value
        for key, value in scenario_dict.items()
    }

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Manual Input
# ============================================================

else:

    st.info(
        "Manual mode is intended for custom testing. "
        "For demonstrations, use Demo Scenario mode."
    )

    position_data = (
        build_credit_position_from_ui()
    )

    provided_fields = sum(
        value is not None
        for value in position_data.values()
    )

    missing_fields = (
        len(position_data)
        - provided_fields
    )

    summary_col1, summary_col2, summary_col3 = (
        st.columns(3)
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

    if input_mode == "Demo Scenario":

        st.caption(
            "Input source: **Demo Scenario**"
        )

    else:

        st.caption(
            "Input source: **Manual Input**"
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

    # --------------------------------------------------------
    # Build position when manual mode is selected
    # --------------------------------------------------------

    if input_mode == "Manual Input":

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

    # --------------------------------------------------------
    # Defensive validation
    # --------------------------------------------------------

    if position is None:

        st.error(
            "No credit position is available."
        )

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

    st.session_state[
        "assessment_input_mode"
    ] = input_mode

    st.session_state[
        "assessment_reporting_mode"
    ] = reporting_mode

    if input_mode == "Demo Scenario":

        st.session_state[
            "assessment_scenario"
        ] = scenario_name


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

assessment_reporting_mode = (
    st.session_state.get(
        "assessment_reporting_mode",
        reporting_mode,
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
            format_field_label(field.name): getattr(
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
            hide_index=True,
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

            if assessment_reporting_mode == "LLM + Fallback":

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

            if assessment_reporting_mode == "LLM + Fallback":

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
        Demo scenarios provide input data only.
        The LLM does not determine assessment status,
        rule severity, thresholds, or credit decisions.
    </div>
    """,
    unsafe_allow_html=True,
)
