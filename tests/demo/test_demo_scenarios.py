import pytest

from app.demo_scenarios import DEMO_SCENARIOS, build_demo_case_data, build_demo_position
from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.services.credit_assessment_case_service import CreditAssessmentCaseService

EXPECTED_FINAL_STATUS = {
    "Healthy Company": "NORMAL",
    "Revenue Deterioration": "ATTENTION",
    "Profitability Stress": "CRITICAL",
    "Leverage Stress": "CRITICAL",
    "Multiple Risk Factors": "CRITICAL",
    "Missing Information": "ATTENTION",
}


@pytest.mark.parametrize("scenario_name", DEMO_SCENARIOS)
def test_demo_scenario_builders_produce_valid_inputs(scenario_name: str) -> None:
    position = build_demo_position(scenario_name)
    profile, behavioural, debt = build_demo_case_data(scenario_name)

    assert position.position_id == DEMO_SCENARIOS[scenario_name]["values"]["position_id"]

    if scenario_name == "Missing Information":
        assert profile is None
        assert behavioural is None
        assert debt is None
    else:
        assert profile is not None
        assert behavioural is not None
        assert debt is not None


def test_demo_scenarios_have_expected_final_statuses(assessment_service) -> None:
    case_service = CreditAssessmentCaseService(
        financial_assessment_service=assessment_service
    )

    for scenario_name, expected_status in EXPECTED_FINAL_STATUS.items():
        position = build_demo_position(scenario_name)
        profile, behavioural, debt = build_demo_case_data(scenario_name)

        case = case_service.assess(
            position,
            customer_profile_data=profile,
            behavioural_data=behavioural,
            debt_sustainability_data=debt,
        )

        assert case.final_assessment is not None
        assert case.final_assessment.status.value == expected_status


def test_demo_case_analysis_agent_preserves_final_assessment_status(
    assessment_service,
) -> None:
    case_service = CreditAssessmentCaseService(
        financial_assessment_service=assessment_service
    )

    for scenario_name, expected_status in EXPECTED_FINAL_STATUS.items():
        position = build_demo_position(scenario_name)
        profile, behavioural, debt = build_demo_case_data(scenario_name)
        case = case_service.assess(
            position,
            customer_profile_data=profile,
            behavioural_data=behavioural,
            debt_sustainability_data=debt,
        )

        analysis = CaseAnalysisAgent().run(case)

        assert analysis.assessment_status.value == expected_status


def test_missing_information_preserves_explicit_limitations(assessment_service) -> None:
    position = build_demo_position("Missing Information")
    profile, behavioural, debt = build_demo_case_data("Missing Information")

    case = CreditAssessmentCaseService(
        financial_assessment_service=assessment_service
    ).assess(
        position,
        customer_profile_data=profile,
        behavioural_data=behavioural,
        debt_sustainability_data=debt,
    )

    assert case.customer_profile.status.value == "NOT_EVALUABLE"
    assert case.behavioural_analysis.status.value == "NOT_EVALUABLE"
    assert case.debt_sustainability.status.value == "NOT_EVALUABLE"
    assert case.financial_analysis.status.value == "ATTENTION"
    assert case.final_assessment is not None
    assert case.final_assessment.status.value == "ATTENTION"
    assert case.final_assessment.limitations
