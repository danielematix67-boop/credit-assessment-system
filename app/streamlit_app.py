import os
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

from app.demo_scenarios import (
    DEMO_SCENARIOS,
    build_demo_position,
)
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
from src.llm.ollama_client import OllamaClient
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
# Environment Detection
# ============================================================

def is_streamlit_cloud() -> bool:
    """
    Detect whether the application is running on
    Streamlit Community Cloud.
    """

    runtime_env = os.getenv(
        "STREAMLIT_RUNTIME_ENV",
        "",
    ).lower()

    sharing_mode = os.getenv(
        "STREAMLIT_SHARING_MODE",
        "",
    ).lower()

    return (
        runtime_env in {
            "cloud",
            "community",
        }
        or sharing_mode == "streamlit"
    )


IS_STREAMLIT_CLOUD = is_streamlit_cloud()


# ============================================================
# Secrets Helpers
# ============================================================

def get_secret(
    key: str,
    default: Any = None,
) -> Any:
    """
    Safely retrieve a Streamlit secret.

    Priority is handled by the caller when environment
    variables are also supported.
    """

    try:
        return st.secrets.get(
            key,
            default,
        )

    except Exception:
        return default


def get_gemini_api_key() -> str | None:
    """
    Retrieve the Gemini API key.

    Priority:
    1. Streamlit secrets
    2. Environment variable
    """

    secret_value = get_secret(
        "GEMINI_API_KEY",
        None,
    )

    if secret_value:
        return str(secret_value)

    environment_value = os.getenv(
        "GEMINI_API_KEY"
    )

    if environment_value:
        return environment_value

    return None


def get_ollama_configuration() -> tuple[str, str]:
    """
    Retrieve Ollama host and model configuration.

    Priority:
    1. Streamlit secrets [ollama] section
    2. Environment variables
    3. Local defaults
    """

    # Streamlit secrets TOML:
    #
    # [ollama]
    # model = "qwen3:4b"
    # host = "http://localhost:11434"

    ollama_section = {}

    try:
        ollama_section = st.secrets.get(
            "ollama",
            {},
        )

    except Exception:
        ollama_section = {}

    ollama_host = (
        ollama_section.get("host")
        or os.getenv(
            "OLLAMA_HOST",
        )
        or "http://localhost:11434"
    )

    ollama_model = (
        ollama_section.get("model")
        or os.getenv(
            "OLLAMA_MODEL",
        )
        or "qwen3:0.6B"
    )

    return (
        str(ollama_host),
        str(ollama_model),
    )

# ============================================================
# Available Reporting Modes
# ============================================================

def get_reporting_modes() -> list[str]:
    """
    Return the reporting modes available in the
    current execution environment.

    Local:
        Deterministic
        Gemini + Fallback
        Ollama + Fallback

    Streamlit Cloud:
        Deterministic
        Gemini + Fallback

    Ollama is deliberately unavailable on Streamlit Cloud
    because localhost inside the cloud container refers to
    the Streamlit Cloud container, not the user's computer.
    """

    if IS_STREAMLIT_CLOUD:
        return [
            "Deterministic",
            "Gemini + Fallback",
        ]

    return [
        "Deterministic",
        "Gemini + Fallback",
        "Ollama + Fallback",
    ]


# ============================================================
# Styling
# ============================================================
#
# Design language:
#   - "Deterministic" surfaces use the BLUE accent (--det-color).
#     These are surfaces produced exclusively by the rule engine
#     / analysis agent and are fully reproducible & traceable.
#   - "AI-assisted" surfaces use the VIOLET accent (--ai-color).
#     These are surfaces where an LLM (Gemini or Ollama) produced
#     natural-language text on top of the deterministic findings.
#   - "Fallback" surfaces use the AMBER accent (--fallback-color).
#     These indicate the LLM was requested but unavailable, so the
#     deterministic generator produced the report instead.
#
# Every card/badge in the app consistently reuses these three
# colors so the provenance of any piece of content is recognizable
# at a glance, without reading the fine print.

st.markdown(
    """
    <style>

    :root {
        --det-color: #2563eb;
        --det-bg: rgba(37, 99, 235, 0.08);
        --ai-color: #7c3aed;
        --ai-bg: rgba(124, 58, 237, 0.08);
        --fallback-color: #b45309;
        --fallback-bg: rgba(180, 83, 9, 0.10);
        --muted: #6b7280;
        --border: rgba(128, 128, 128, 0.20);
    }

    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    h1, h2, h3 {
        letter-spacing: -0.01em;
    }

    .app-subtitle {
        color: var(--muted);
        font-size: 1rem;
        margin-top: -0.4rem;
        margin-bottom: 1.2rem;
    }

    /* ---------------------------------------------------- */
    /* Provenance badges                                     */
    /* ---------------------------------------------------- */

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.22rem 0.65rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 650;
        letter-spacing: 0.01em;
        border: 1px solid transparent;
        white-space: nowrap;
    }

    .badge-det {
        color: var(--det-color);
        background: var(--det-bg);
        border-color: rgba(37, 99, 235, 0.25);
    }

    .badge-ai {
        color: var(--ai-color);
        background: var(--ai-bg);
        border-color: rgba(124, 58, 237, 0.25);
    }

    .badge-fallback {
        color: var(--fallback-color);
        background: var(--fallback-bg);
        border-color: rgba(180, 83, 9, 0.28);
    }

    .badge-row {
        margin-bottom: 0.6rem;
    }

    /* ---------------------------------------------------- */
    /* Pipeline / workflow diagram                           */
    /* ---------------------------------------------------- */

    .pipeline-wrap {
        display: flex;
        align-items: stretch;
        gap: 0.4rem;
        margin: 0.4rem 0 0.8rem 0;
    }

    .pipeline-step {
        flex: 1;
        padding: 1rem 0.9rem;
        border-radius: 0.7rem;
        border: 1.5px solid var(--border);
        background: rgba(128, 128, 128, 0.025);
        min-height: 108px;
        position: relative;
    }

    .pipeline-step.det {
        border-color: rgba(37, 99, 235, 0.35);
        background: var(--det-bg);
    }

    .pipeline-step.ai {
        border-color: rgba(124, 58, 237, 0.35);
        background: var(--ai-bg);
    }

    .pipeline-arrow {
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--muted);
        font-size: 1.1rem;
        padding: 0 0.1rem;
    }

    .pipeline-number {
        font-size: 0.72rem;
        font-weight: 750;
        color: var(--muted);
        letter-spacing: 0.06em;
    }

    .pipeline-title {
        font-weight: 650;
        margin-top: 0.25rem;
        font-size: 0.92rem;
    }

    .pipeline-description {
        color: var(--muted);
        font-size: 0.76rem;
        margin-top: 0.1rem;
        line-height: 1.35;
    }

    .pipeline-legend {
        display: flex;
        gap: 1.4rem;
        margin-top: 0.4rem;
        margin-bottom: 0.2rem;
        flex-wrap: wrap;
    }

    .pipeline-legend-item {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.78rem;
        color: var(--muted);
    }

    .legend-dot {
        width: 0.65rem;
        height: 0.65rem;
        border-radius: 50%;
        display: inline-block;
    }

    .legend-dot.det { background: var(--det-color); }
    .legend-dot.ai { background: var(--ai-color); }

    /* ---------------------------------------------------- */
    /* Generic cards                                          */
    /* ---------------------------------------------------- */

    .scenario-card {
        padding: 1.2rem 1.4rem;
        border-radius: 0.7rem;
        border: 1px solid var(--border);
        background: rgba(128, 128, 128, 0.025);
        margin-bottom: 1rem;
    }

    .scenario-title {
        font-size: 1.1rem;
        font-weight: 650;
        margin-bottom: 0.4rem;
    }

    .scenario-description {
        color: var(--muted);
        font-size: 0.88rem;
        line-height: 1.5;
    }

    .data-introduction {
        color: var(--muted);
        font-size: 0.88rem;
        line-height: 1.5;
        margin-bottom: 1rem;
    }

    .data-note {
        padding: 0.9rem 1rem;
        border-radius: 0.6rem;
        border: 1px solid var(--border);
        background: rgba(128, 128, 128, 0.025);
        margin-bottom: 1rem;
        font-size: 0.85rem;
        color: var(--muted);
    }

    .provenance-panel {
        border-radius: 0.75rem;
        border: 1px solid var(--border);
        padding: 1.1rem 1.3rem;
        margin-bottom: 1.2rem;
        background: rgba(128, 128, 128, 0.02);
    }

    .provenance-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.45rem 0;
        border-bottom: 1px dashed var(--border);
        font-size: 0.87rem;
    }

    .provenance-row:last-child {
        border-bottom: none;
    }

    .provenance-label {
        color: inherit;
        font-weight: 550;
    }

    .metric-description {
        color: var(--muted);
        font-size: 0.78rem;
    }

    .section-card {
        border-radius: 0.7rem;
        border: 1.5px solid var(--border);
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
    }

    .section-card.det {
        border-left: 4px solid var(--det-color);
    }

    .section-card.ai {
        border-left: 4px solid var(--ai-color);
    }

    .section-card.fallback {
        border-left: 4px solid var(--fallback-color);
    }

    .footer {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border);
        color: var(--muted);
        font-size: 0.78rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Badge / Provenance Helpers
# ============================================================

def render_badge(
    label: str,
    kind: str = "det",
) -> str:
    """
    Return the HTML markup for a small provenance badge.

    kind: "det" | "ai" | "fallback"
    """

    icons = {
        "det": "🔒",
        "ai": "🤖",
        "fallback": "⚠️",
    }

    css_class = {
        "det": "badge-det",
        "ai": "badge-ai",
        "fallback": "badge-fallback",
    }[kind]

    icon = icons[kind]

    return (
        f'<span class="badge {css_class}">'
        f'{icon} {label}</span>'
    )


def show_badge(
    label: str,
    kind: str = "det",
) -> None:

    st.markdown(
        f'<div class="badge-row">{render_badge(label, kind)}</div>',
        unsafe_allow_html=True,
    )


def reporting_mode_badge_kind(
    reporting_mode: str,
) -> str:
    """
    Map a reporting mode selection to its *intended* badge kind,
    before knowing whether a fallback actually occurred.
    """

    if reporting_mode == "Deterministic":
        return "det"

    return "ai"


# ============================================================
# CreditPosition Introspection
# ============================================================

def get_credit_position_fields():
    """
    Return the fields defined by the CreditPosition dataclass.

    CreditPosition remains the source of truth for the input schema.
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

def unwrap_optional(
    field_type: Any,
) -> tuple[Any, bool]:
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

def format_field_label(
    field_name: str,
) -> str:

    special_terms = {
        "ebitda": "EBITDA",
        "nfp": "nfp",
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

    descriptions = {
        "position_id": (
            "Unique identifier of the credit position."
        ),

        "revenue": (
            "Total company revenue."
        ),

        "change_in_finished_goods_inventory": (
            "Change in finished goods inventory."
        ),

        "operating_grants": (
            "Operating grants received by the company."
        ),

        "net_purchases": (
            "Net purchases of raw materials and goods."
        ),

        "change_in_raw_materials_inventory": (
            "Change in raw materials inventory."
        ),

        "costs_for_services_and_third_party_assets": (
            "Costs related to services and third-party assets."
        ),

        "personnel_costs": (
            "Personnel and employee-related costs."
        ),

        "depreciation_tangible_assets": (
            "Depreciation of tangible fixed assets."
        ),

        "working_capital_impairments": (
            "Impairments related to working capital."
        ),

        "operating_provisions": (
            "Operating provisions and related adjustments."
        ),

        "other_income_expenses_balance": (
            "Net balance of other operating income and expenses."
        ),

        "operating_value_added": (
            "Derived operating value added."
        ),

        "gross_operating_margin": (
            "Gross operating margin generated by the company."
        ),

        "net_operating_margin": (
            "Net operating margin after operating costs."
        ),

        "ebitda": (
            "Earnings before interest, taxes, "
            "depreciation and amortization."
        ),

        "profit_loss": (
            "Reported profit or loss for the company."
        ),

        "ebitda_margin": (
            "EBITDA expressed as a percentage of revenue."
        ),

        "ebitda_inventory_contribution": (
            "Contribution of inventory changes to EBITDA."
        ),

        "nfp_to_ebitda": (
            "Net financial position relative to EBITDA; "
            "a leverage indicator."
        ),

        "interest_expense": (
            "Financial expense related to interest."
        ),

        "revenue_growth": (
            "Year-over-year change in company revenue."
        ),
    }

    return descriptions.get(
        field_name,
        f"Input value for {format_field_label(field_name)}.",
    )


def format_field_value(
    field_name: str,
    value: Any,
) -> str:

    if value is None:
        return "Not available"

    if field_name == "position_id":
        return str(value)

    if field_name in {
        "revenue_growth",
        "ebitda_margin",
    }:
        return f"{float(value):.1%}"

    if field_name in {
        "revenue",
        "change_in_finished_goods_inventory",
        "operating_grants",
        "net_purchases",
        "change_in_raw_materials_inventory",
        "costs_for_services_and_third_party_assets",
        "personnel_costs",
        "depreciation_tangible_assets",
        "working_capital_impairments",
        "operating_provisions",
        "other_income_expenses_balance",
        "operating_value_added",
        "gross_operating_margin",
        "net_operating_margin",
        "ebitda",
        "profit_loss",
        "ebitda_inventory_contribution",
        "interest_expense",
    }:
        return f"€{float(value):,.0f}"

    if field_name == "nfp_to_ebitda":
        return f"{float(value):.2f}x"

    if isinstance(value, float):
        return f"{value:,.4f}"

    return str(value)


def get_field_unit(
    field_name: str,
) -> str:

    units = {
        "position_id": "Identifier",

        "revenue_growth": "%",
        "ebitda_margin": "%",

        "revenue": "EUR",
        "change_in_finished_goods_inventory": "EUR",
        "operating_grants": "EUR",
        "net_purchases": "EUR",
        "change_in_raw_materials_inventory": "EUR",
        "costs_for_services_and_third_party_assets": "EUR",
        "personnel_costs": "EUR",
        "depreciation_tangible_assets": "EUR",
        "working_capital_impairments": "EUR",
        "operating_provisions": "EUR",
        "other_income_expenses_balance": "EUR",
        "operating_value_added": "EUR",
        "gross_operating_margin": "EUR",
        "net_operating_margin": "EUR",
        "ebitda": "EUR",
        "profit_loss": "EUR",
        "ebitda_inventory_contribution": "EUR",
        "interest_expense": "EUR",

        "nfp_to_ebitda": "x",
    }

    return units.get(
        field_name,
        "",
    )


# ============================================================
# Scenario / Position Data Presentation
# ============================================================

def build_scenario_data_table(
    position: CreditPosition,
) -> list[dict[str, str]]:

    rows = []

    for field in fields(position):

        field_name = field.name

        value = getattr(
            position,
            field_name,
        )

        rows.append(
            {
                "Financial Indicator": format_field_label(
                    field_name
                ),
                "Value": format_field_value(
                    field_name,
                    value,
                ),
                "Unit": get_field_unit(
                    field_name
                ),
                "Description": format_field_description(
                    field_name
                ),
            }
        )

    return rows


def display_position_table(
    position: CreditPosition,
) -> None:

    position_data = build_scenario_data_table(
        position
    )

    st.dataframe(
        position_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Financial Indicator": st.column_config.TextColumn(
                "Financial Indicator",
                width="medium",
            ),
            "Value": st.column_config.TextColumn(
                "Value",
                width="medium",
            ),
            "Unit": st.column_config.TextColumn(
                "Unit",
                width="small",
            ),
            "Description": st.column_config.TextColumn(
                "What it represents",
                width="large",
            ),
        },
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

    description = format_field_description(
        field_name
    )

    if resolved_type is str and not is_optional:

        st.caption(description)

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
            key=(
                f"credit_position_{field_name}_provided"
            ),
        )

        if not provided:
            return None

        st.caption(description)

        return st.text_input(
            label,
            value=(
                ""
                if default is None
                else str(default)
            ),
            key=(
                f"credit_position_{field_name}_value"
            ),
        )

    if resolved_type is int and not is_optional:

        st.caption(description)

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

        st.caption(description)

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

    reporting_modes = get_reporting_modes()

    reporting_mode = st.radio(
        "Reporting Mode",
        options=reporting_modes,
        index=0,
    )

    st.divider()

    # --------------------------------------------------------
    # Provenance Legend
    # --------------------------------------------------------

    st.subheader("How to read this app")

    st.markdown(
        f"""
        <div class="pipeline-legend">
            <div class="pipeline-legend-item">
                <span class="legend-dot det"></span>
                Deterministic — rule engine, fully traceable
            </div>
            <div class="pipeline-legend-item">
                <span class="legend-dot ai"></span>
                AI-assisted — language generated by an LLM
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "Every section of the app carries one of these badges "
        "so you always know whether content is guaranteed "
        "reproducible or was phrased by a language model."
    )

    st.divider()

    # --------------------------------------------------------
    # Environment Information
    # --------------------------------------------------------

    st.subheader(
        "Execution Environment"
    )

    if IS_STREAMLIT_CLOUD:

        st.info(
            "☁️ Streamlit Community Cloud"
        )

        st.caption(
            "Ollama is disabled in the cloud. "
            "The application can use deterministic reporting "
            "or Gemini when configured."
        )

    else:

        st.success(
            "💻 Local Environment"
        )

        st.caption(
            "Ollama is available as a local reporting option."
        )

    st.divider()

    # --------------------------------------------------------
    # Architecture Guarantees
    # --------------------------------------------------------

    st.subheader(
        "Architecture Guarantees"
    )

    guarantee_items = [
        ("⚖️", "Deterministic decision layer",
         "The rule engine is the sole authority for status, "
         "severity and findings."),
        ("🧭", "Controlled AI usage",
         "The LLM only rewrites findings into prose — it never "
         "decides the outcome."),
        ("🔗", "Traceability",
         "Every report finding links back to a specific "
         "deterministic rule."),
        ("🛟", "Automatic fallback",
         "If the LLM is unavailable, the deterministic report "
         "generator takes over transparently."),
    ]

    for icon, title, description in guarantee_items:

        st.markdown(
            f"**{icon} {title}**  \n"
            f"<span style='color:var(--muted); font-size:0.82rem;'>"
            f"{description}</span>",
            unsafe_allow_html=True,
        )

    st.divider()

    # --------------------------------------------------------
    # Reporting Mode Description
    # --------------------------------------------------------

    st.subheader("Selected Reporting Mode")

    if reporting_mode == "Gemini + Fallback":

        gemini_key = get_gemini_api_key()

        show_badge("AI-assisted (Gemini)", "ai")

        if gemini_key:

            st.success(
                "Gemini reporting enabled"
            )

            st.caption(
                "Gemini is used exclusively for executive "
                "report generation."
            )

        else:

            st.warning(
                "Gemini selected, but GEMINI_API_KEY "
                "is not configured."
            )

            st.caption(
                "The deterministic fallback will be used "
                "automatically until the key is configured."
            )

    elif reporting_mode == "Ollama + Fallback":

        ollama_host, ollama_model = (
            get_ollama_configuration()
        )

        show_badge("AI-assisted (Local LLM)", "ai")

        st.success(
            "Local LLM reporting enabled"
        )

        st.caption(
            f"Model: `{ollama_model}`"
        )

        st.caption(
            f"Host: `{ollama_host}`"
        )

        st.caption(
            "The configured local Ollama model is used "
            "exclusively for executive report generation."
        )

    else:

        show_badge("Fully deterministic", "det")

        st.info(
            "Deterministic reporting enabled"
        )

        st.caption(
            "No external LLM call is required — the executive "
            "report is generated by the same rule engine as "
            "the findings."
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

    # --------------------------------------------------------
    # Deterministic
    # --------------------------------------------------------

    if reporting_mode == "Deterministic":

        reporting_agent = ReportingAgent(
            report_generator=(
                deterministic_report_generator
            ),
        )

    # --------------------------------------------------------
    # Gemini
    # --------------------------------------------------------

    elif reporting_mode == "Gemini + Fallback":

        api_key = get_gemini_api_key()

        if not api_key:

            st.error(
                "GEMINI_API_KEY is not configured."
            )

            st.info(
                "Configure GEMINI_API_KEY in "
                ".streamlit/secrets.toml when running locally "
                "or in Streamlit Cloud Secrets when deployed."
            )

            st.stop()

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

    # --------------------------------------------------------
    # Ollama
    # --------------------------------------------------------

    elif reporting_mode == "Ollama + Fallback":

        if IS_STREAMLIT_CLOUD:

            st.error(
                "Ollama is not available on Streamlit Cloud."
            )

            st.info(
                "Select Deterministic or Gemini + Fallback."
            )

            st.stop()

        ollama_host, ollama_model = (
            get_ollama_configuration()
        )

        llm_client = OllamaClient(
            model=ollama_model,
            host=ollama_host,
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

        raise ValueError(
            f"Unsupported reporting mode: "
            f"{reporting_mode}"
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
        controlled, clearly-labelled AI-assisted reporting.
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
    "End-to-end processing architecture. Blue steps are fully "
    "deterministic; the violet step is where an LLM may "
    "generate prose, always constrained by the deterministic "
    "output next to it."
)

workflow_steps = [
    ("01", "Credit Data", "Structured financial input", "det"),
    ("02", "Rule Engine", "Deterministic thresholds & severity", "det"),
    ("03", "Analysis Agent", "Rule-based interpretation", "det"),
    ("04", "Reporting Agent", "LLM prose, or deterministic fallback", "ai"),
    ("05", "Assessment Report", "Findings + executive summary", "det"),
]

pipeline_html = '<div class="pipeline-wrap">'

for i, (number, title, description, kind) in enumerate(workflow_steps):

    pipeline_html += (
        f'<div class="pipeline-step {kind}">'
        f'<div class="pipeline-number">{number}</div>'
        f'<div class="pipeline-title">{title}</div>'
        f'<div class="pipeline-description">{description}</div>'
        f'</div>'
    )

    if i < len(workflow_steps) - 1:
        pipeline_html += '<div class="pipeline-arrow">→</div>'

pipeline_html += "</div>"

st.markdown(pipeline_html, unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="pipeline-legend">
        <div class="pipeline-legend-item">
            <span class="legend-dot det"></span> Deterministic
        </div>
        <div class="pipeline-legend-item">
            <span class="legend-dot ai"></span> AI-assisted
            (with deterministic fallback)
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
# Position Variables
# ============================================================

position: CreditPosition | None = None
position_data: dict[str, Any] | None = None


# ============================================================
# Demo Scenario Input
# ============================================================

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

    st.markdown(
        """
        <div class="data-introduction">
            The following values represent the financial data
            provided as input to the credit assessment system.
            They are <strong>not assessment results</strong>.
            The deterministic rule engine evaluates these inputs
            against the configured rules and thresholds during
            the assessment workflow.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="data-note">
            <strong>Input data vs. assessment result</strong><br>
            Financial indicators supplied to the system are
            displayed separately from rule findings, severity
            and assessment status. These assessment outputs
            are calculated by the deterministic decision layer.
        </div>
        """,
        unsafe_allow_html=True,
    )

    scenario_data = build_scenario_data_table(
        position
    )

    st.dataframe(
        scenario_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Financial Indicator": st.column_config.TextColumn(
                "Financial Indicator",
                width="medium",
            ),
            "Value": st.column_config.TextColumn(
                "Value",
                width="medium",
            ),
            "Unit": st.column_config.TextColumn(
                "Unit",
                width="small",
            ),
            "Description": st.column_config.TextColumn(
                "What it represents",
                width="large",
            ),
        },
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

    st.caption("Reporting mode")

    show_badge(
        reporting_mode,
        reporting_mode_badge_kind(reporting_mode),
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

    if position is None:

        st.error(
            "No credit position is available."
        )

        st.stop()

    workflow = create_workflow(
        reporting_mode=reporting_mode,
    )

    if reporting_mode == "Gemini + Fallback":

        spinner_message = (
            "Executing deterministic assessment "
            "and generating Gemini-assisted report..."
        )

    elif reporting_mode == "Ollama + Fallback":

        _, ollama_model = (
            get_ollama_configuration()
        )

        spinner_message = (
            "Executing deterministic assessment "
            f"and generating local LLM report "
            f"using {ollama_model}..."
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


if result is not None:

    st.divider()

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

    selected_reporting_mode = (
        st.session_state.get(
            "assessment_reporting_mode",
            reporting_mode,
        )
    )

    # Resolve the actual badge for the executive report,
    # accounting for a possible fallback.
    if selected_reporting_mode == "Deterministic":
        report_badge_kind = "det"
        report_badge_label = "Deterministic"
    elif generator_used == "FALLBACK":
        report_badge_kind = "fallback"
        report_badge_label = "Deterministic fallback (LLM unavailable)"
    elif generator_used == "PRIMARY":
        if selected_reporting_mode == "Gemini + Fallback":
            report_badge_kind = "ai"
            report_badge_label = "AI-generated (Gemini)"
        elif selected_reporting_mode == "Ollama + Fallback":
            _, _ollama_model_badge = get_ollama_configuration()
            report_badge_kind = "ai"
            report_badge_label = f"AI-generated (Local LLM · {_ollama_model_badge})"
        else:
            report_badge_kind = "det"
            report_badge_label = "Deterministic"
    else:
        report_badge_kind = "fallback"
        report_badge_label = "Unknown"

    # ========================================================
    # Provenance Panel — the "who produced what" summary
    # ========================================================

    st.subheader("Provenance of This Assessment")

    st.caption(
        "A quick summary of which layer produced each part "
        "of the output below."
    )

    provenance_col1, provenance_col2 = st.columns(2)

    with provenance_col1:

        st.markdown(
            f"""
            <div class="section-card det">
                <div style="font-weight:650; margin-bottom:0.3rem;">
                    Assessment Status &amp; Rule Findings
                </div>
                {render_badge("Deterministic — Rule Engine", "det")}
                <div class="metric-description" style="margin-top:0.5rem;">
                    Fixed thresholds, rule-based severity. Identical
                    input always produces identical output.
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
                {render_badge(report_badge_label, report_badge_kind)}
                <div class="metric-description" style="margin-top:0.5rem;">
                    Natural-language phrasing only — it cannot alter
                    the assessment status or findings above.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
    # Assessed Credit Position
    # ========================================================

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

        if generator_used == "FALLBACK":

            st.warning(
                "⚠ Reporting Fallback"
            )

            st.caption(
                "Deterministic fallback generator used"
            )

        elif generator_used == "PRIMARY":

            if selected_reporting_mode == "Gemini + Fallback":

                st.success(
                    "✓ Gemini Reporting"
                )

                st.caption(
                    "AI-assisted report generated"
                )

            elif selected_reporting_mode == "Ollama + Fallback":

                _, ollama_model = (
                    get_ollama_configuration()
                )

                st.success(
                    "✓ Local LLM Reporting"
                )

                st.caption(
                    f"Model: {ollama_model}"
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
            "🔒 Rule Findings",
            "🔒 Analysis",
            f"{'🤖' if report_badge_kind == 'ai' else ('⚠️' if report_badge_kind == 'fallback' else '🔒')} Executive Report",
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

        show_badge("Determined by rule engine only", "det")

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
            f"Reporting layer: **{selected_reporting_mode}**"
        )

        show_badge(report_badge_label, report_badge_kind)

        if selected_reporting_mode == "Ollama + Fallback":

            _, model = get_ollama_configuration()

            st.caption(
                f"Configured local model: `{model}`"
            )

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
                        <li>Fixed thresholds</li>
                        <li>Rule-based severity</li>
                        <li>Traceable findings</li>
                        <li>Fixed assessment status</li>
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
                    {render_badge("AI-assisted, with fallback", "ai")}
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

    # ========================================================
    # Rule Findings Tab
    # ========================================================

    with findings_tab:

        st.markdown(
            "### Deterministic Rule Engine Findings"
        )

        show_badge("Deterministic — fully traceable", "det")

        st.caption(
            "These findings constitute the factual basis "
            "of the assessment. No LLM is involved in this tab."
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

        show_badge("Deterministic — rule-based interpretation", "det")

        st.caption(
            "Structured interpretation of the deterministic "
            "assessment output. No LLM is involved in this tab."
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

        show_badge(report_badge_label, report_badge_kind)

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

            if selected_reporting_mode == "Gemini + Fallback":

                st.success(
                    "Gemini generated the executive report "
                    "successfully."
                )

                st.caption(
                    "The LLM was used exclusively for report "
                    "generation. The assessment outcome remains "
                    "deterministic."
                )

            elif selected_reporting_mode == "Ollama + Fallback":

                _, ollama_model = (
                    get_ollama_configuration()
                )

                st.success(
                    "Local LLM generated the executive report "
                    "successfully."
                )

                st.caption(
                    f"Configured model: `{ollama_model}`"
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

            show_badge("Deterministic — sourced from rule engine", "det")

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
        with controlled, clearly-labelled AI-assisted reporting.
        <br>
        Demo scenarios provide input data only.
        The LLM does not determine assessment status,
        rule severity, thresholds, or credit decisions —
        it only phrases the executive summary, and every
        such section is marked with an 🤖 AI badge.
    </div>
    """,
    unsafe_allow_html=True,
)