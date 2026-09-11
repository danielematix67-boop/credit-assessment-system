from types import SimpleNamespace

import pytest

from app.demo_scenarios import DEMO_SCENARIOS, build_demo_case_data, build_demo_position
from app.ui.results.helpers import get_rule_results
from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.services.credit_assessment_case_service import CreditAssessmentCaseService

EXPECTED_FINAL_STATUS = {
    "01 · Baseline": "NORMAL",
    "02 · Customer Profile Risk": "CRITICAL",
    "03 · Revenue & Profitability Risk": "CRITICAL",
    "04 · Leverage & Interest Risk": "CRITICAL",
    "05 · Profitability Quality Risk": "ATTENTION",
    "06 · Behavioural Risk": "CRITICAL",
    "07 · Debt Sustainability Risk": "CRITICAL",
    "08 · Integrated Credit Stress": "CRITICAL",
    "09 · Data Availability": "ATTENTION",
}

EXPECTED_TRIGGERED_RULES = {
    "01 · Baseline": set(),
    "02 · Customer Profile Risk": {"CP001", "CP002", "CP003"},
    "03 · Revenue & Profitability Risk": {"R001", "R002", "R003", "R007"},
    "04 · Leverage & Interest Risk": {"R004", "R005", "R007"},
    "05 · Profitability Quality Risk": {"R006"},
    "06 · Behavioural Risk": {"B001", "B002", "B003", "B004"},
    "07 · Debt Sustainability Risk": {"DS001", "DS002", "DS003"},
    "08 · Integrated Credit Stress": {
        "CP001",
        "CP002",
        "R001",
        "R002",
        "R003",
        "R007",
        "B001",
        "B002",
        "B003",
        "B004",
        "DS001",
        "DS002",
        "DS003",
    },
    "09 · Data Availability": set(),
}

EXPECTED_UI_RULE_IDS = {
    "CP001",
    "CP002",
    "CP003",
    "B001",
    "B002",
    "B003",
    "B004",
    "DS001",
    "DS002",
    "DS003",
    "R001",
    "R002",
    "R003",
    "R004",
    "R005",
    "R006",
    "R007",
}


@pytest.mark.parametrize("scenario_name", DEMO_SCENARIOS)
def test_demo_scenario_builders_produce_valid_inputs(scenario_name: str) -> None:
    position = build_demo_position(scenario_name)
    profile, behavioural, debt = build_demo_case_data(scenario_name)

    assert position.position_id == DEMO_SCENARIOS[scenario_name]["values"]["position_id"]

    if scenario_name == "09 · Data Availability":
        assert profile is None
        assert behavioural is None
        assert debt is None
    else:
        assert profile is not None
        assert behavioural is not None
        assert debt is not None


def _triggered_rule_ids(case) -> set[str]:
    """Collect triggered deterministic rule IDs across all assessment areas."""
    sections = (
        case.customer_profile,
        case.financial_analysis,
        case.behavioural_analysis,
        case.debt_sustainability,
    )
    return {
        result.rule_id
        for section in sections
        for result in section.evidence
        if result.is_triggered
    }


def test_demo_scenarios_cover_expected_triggered_rule_ids(assessment_service) -> None:
    case_service = CreditAssessmentCaseService(
        financial_assessment_service=assessment_service
    )

    for scenario_name, expected_rule_ids in EXPECTED_TRIGGERED_RULES.items():
        position = build_demo_position(scenario_name)
        profile, behavioural, debt = build_demo_case_data(scenario_name)
        case = case_service.assess(
            position,
            customer_profile_data=profile,
            behavioural_data=behavioural,
            debt_sustainability_data=debt,
        )

        assert _triggered_rule_ids(case) == expected_rule_ids


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
    position = build_demo_position("09 · Data Availability")
    profile, behavioural, debt = build_demo_case_data("09 · Data Availability")

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
    assert case.financial_analysis.status.value == "NOT_EVALUABLE"
    assert case.final_assessment is not None
    assert case.final_assessment.status.value == "ATTENTION"
    assert case.final_assessment.limitations


def test_ui_rule_evidence_source_covers_all_registered_demo_rules(
    assessment_service,
) -> None:
    """Ensure the Results-page evidence source exposes every deterministic rule ID."""
    case_service = CreditAssessmentCaseService(
        financial_assessment_service=assessment_service
    )

    displayed_rule_ids: set[str] = set()
    for scenario_name in DEMO_SCENARIOS:
        position = build_demo_position(scenario_name)
        profile, behavioural, debt = build_demo_case_data(scenario_name)
        case = case_service.assess(
            position,
            customer_profile_data=profile,
            behavioural_data=behavioural,
            debt_sustainability_data=debt,
        )
        rule_results = [
            rule
            for section in (
                case.customer_profile,
                case.financial_analysis,
                case.behavioural_analysis,
                case.debt_sustainability,
            )
            for rule in section.evidence
        ]
        result = SimpleNamespace(assessment=SimpleNamespace(rule_results=rule_results))
        displayed_rule_ids.update(rule.rule_id for rule in get_rule_results(result))

    assert displayed_rule_ids == EXPECTED_UI_RULE_IDS
