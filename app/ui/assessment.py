import streamlit as st

from app.demo_scenarios import build_demo_case_data
from app.workflow.assessment_workflow_factory import create_workflow
from app.workflow.runner import run_assessment
from src.models.position import CreditPosition


def get_spinner_message(reporting_mode: str) -> str:
    """Return the spinner message for the selected reporting mode."""

    if reporting_mode == "Gemini + Fallback":
        return (
            "Executing deterministic assessment "
            "and generating Gemini-assisted report..."
        )

    if reporting_mode == "Ollama + Fallback":
        return "Executing deterministic assessment and generating local LLM report..."

    return "Executing deterministic assessment workflow..."


def build_credit_position(
    position: CreditPosition | None,
    position_data: dict,
    input_mode: str,
) -> CreditPosition:
    """Build and validate the CreditPosition used by the assessment."""

    if input_mode == "Manual Input":
        try:
            return CreditPosition(**position_data)
        except TypeError as error:
            raise TypeError("Unable to construct CreditPosition.") from error

    if position is None:
        raise ValueError("No credit position is available.")

    return position


def execute_assessment(
    position: CreditPosition,
    reporting_mode: str,
    scenario_name: str | None = None,
):
    """Create and execute the assessment workflow."""

    try:
        workflow = create_workflow(reporting_mode=reporting_mode)
    except Exception as error:
        st.error("Unable to create the assessment workflow.")
        st.exception(error)
        st.stop()

    spinner_message = get_spinner_message(reporting_mode)

    with st.spinner(spinner_message):
        try:
            if scenario_name:
                (
                    customer_profile_data,
                    behavioural_data,
                    debt_sustainability_data,
                ) = build_demo_case_data(scenario_name)
                result = run_assessment(
                    workflow,
                    position,
                    behavioural_data=behavioural_data,
                    debt_sustainability_data=debt_sustainability_data,
                    customer_profile_data=customer_profile_data,
                )
            else:
                result = run_assessment(
                    workflow,
                    position,
                    behavioural_data=st.session_state.get("manual_behavioural_data"),
                    debt_sustainability_data=st.session_state.get(
                        "manual_debt_sustainability_data"
                    ),
                    customer_profile_data=st.session_state.get(
                        "manual_customer_profile_data"
                    ),
                )

        except Exception as error:
            st.error("Assessment execution failed.")
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
    st.session_state["assessment_reporting_mode"] = reporting_mode

    if input_mode == "Demo Scenario":
        st.session_state["assessment_scenario"] = scenario_name
