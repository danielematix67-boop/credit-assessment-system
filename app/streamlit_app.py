# ruff: noqa: E402

import sys
from pathlib import Path


# ============================================================
# Project Path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# External Imports
# ============================================================

import streamlit as st


# ============================================================
# Application Imports
# ============================================================

from app.ui.assessment import (
    execute_assessment,
    store_assessment_result,
)

from app.ui.assessment_configuration import (
    render_assessment_configuration,
)

from app.ui.input_source import (
    render_credit_data_source,
)

from app.ui.results import (
    render_results,
)

from app.ui.sidebar import (
    render_sidebar,
)

from app.ui.styles import (
    apply_styles,
)

from app.ui.workflow_view import (
    render_workflow_architecture,
)

from app.ui.layout import (
    render_footer,
    render_header,
)

from src.models.position import CreditPosition


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="Credit Assessment System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Styles
# ============================================================

apply_styles()


# ============================================================
# Sidebar
# ============================================================

reporting_mode = render_sidebar()


# ============================================================
# Header
# ============================================================

render_header()

# ============================================================
# Workflow Architecture
# ============================================================

render_workflow_architecture()

st.divider()


# ============================================================
# Credit Data Source
# ============================================================

(
    position,
    position_data,
    input_mode,
    scenario_name,
) = render_credit_data_source()


# ============================================================
# Assessment Configuration
# ============================================================

run_button = render_assessment_configuration(
    reporting_mode=reporting_mode,
    input_mode=input_mode,
)


# ============================================================
# Execute Assessment
# ============================================================

if run_button:

    # --------------------------------------------------------
    # Build CreditPosition from Manual Input
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
    # Validate Position
    # --------------------------------------------------------

    if position is None:

        st.error(
            "No credit position is available."
        )

        st.stop()

    # --------------------------------------------------------
    # Execute Assessment
    # --------------------------------------------------------

    result = execute_assessment(
        position=position,
        reporting_mode=reporting_mode,
    )

    # --------------------------------------------------------
    # Store Assessment Result
    # --------------------------------------------------------

    store_assessment_result(
        result=result,
        position=position,
        input_mode=input_mode,
        reporting_mode=reporting_mode,
        scenario_name=(
            scenario_name
            if input_mode == "Demo Scenario"
            else None
        ),
    )


# ============================================================
# Results
# ============================================================

result = st.session_state.get(
    "assessment_result"
)

assessment_position = st.session_state.get(
    "assessment_position"
)

selected_reporting_mode = (
    st.session_state.get(
        "assessment_reporting_mode",
        reporting_mode,
    )
)

render_results(
    result=result,
    assessment_position=assessment_position,
    selected_reporting_mode=selected_reporting_mode,
)


# ============================================================
# Footer
# ============================================================

render_footer()