import streamlit as st

from src.models.position import CreditPosition

from app.workflow.assessment_workflow_factory import create_workflow
from app.workflow.runner import run_assessment


def get_spinner_message(reporting_mode: str) -> str:
    """Return the spinner message for the selected reporting mode."""

    if reporting_mode == "Gemini + Fallback":
        return (
            "Executing deterministic assessment "
            "and generating Gemini-assisted report..."
        )

    if reporting_mode == "Ollama + Fallback":
        return (
            "Executing deterministic assessment "
            "and generating local LLM report..."
        )

    return "Executing deterministic assessment workflow..."


def execute_assessment(
    position: CreditPosition,
    reporting_mode: str,
):
    """Create and execute the assessment workflow."""

    try:
        workflow = create_workflow(
            reporting_mode=reporting_mode,
        )

    except Exception as error:
        st.error(
            "Unable to create the assessment workflow."
        )
        st.exception(error)
        st.stop()

    spinner_message = get_spinner_message(
        reporting_mode
    )

    with st.spinner(spinner_message):

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

    return result


def store_assessment_result(
    result,
    position: CreditPosition,
    input_mode: str,
    reporting_mode: str,
    scenario_name: str | None = None,
) -> None:
    """Store the latest assessment data in Streamlit session state."""

    st.session_state["assessment_result"] = result

    st.session_state["assessment_position"] = position

    st.session_state["assessment_input_mode"] = input_mode

    st.session_state["assessment_reporting_mode"] = (
        reporting_mode
    )

    if input_mode == "Demo Scenario":
        st.session_state["assessment_scenario"] = (
            scenario_name
        )