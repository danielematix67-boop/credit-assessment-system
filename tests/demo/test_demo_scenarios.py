from types import SimpleNamespace

from app.demo_scenarios import DEMO_SCENARIOS, build_demo_case_data, build_demo_position
from app.ui.results.helpers import get_rule_results
from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.services.credit_assessment_case_service import CreditAssessmentCaseService

SCENARIO_NAME = "01 · Complete Credit Assessment"
EXPECTED_FINAL_STATUS = "CRITICAL"

EXPECTED_TRIGGERED_RULES = {
    "CP001", "CP002", "CP003",
    "R001", "R002", "R003", "R007",
    "B001", "B002", "B003", "B004",
    "DS001", "DS002", "DS003",
}

EXPECTED_UI_RULE_IDS = {
    "CP001", "CP002", "CP003",
    "B001", "B002", "B003", "B004",
    "DS001", "DS002", "DS003",
    "R001", "R002", "R003", "R004", "R005", "R006", "R007",
}


def _build_demo_case(assessment_service):
    case_service = CreditAssessmentCaseService(
        financial_assessment_service=assessment_service
    )
    position = build_demo_position(SCENARIO_NAME)
    profile, behavioural, debt = build_demo_case_data(SCENARIO_NAME)
    return case_service.assess(
        position,
        customer_profile_data=profile,
        behavioural_data=behavioural,
        debt_sustainability_data=debt,
    )


def _triggered_rule_ids(case) -> set[str]:
    """Collect triggered deterministic rule IDs across all assessment areas."""
    return {
        result.rule_id
        for section in (
            case.customer_profile,
            case.financial_analysis,
            case.behavioural_analysis,
            case.debt_sustainability,
        )
        for result in section.evidence
        if result.is_triggered
    }


def test_demo_catalog_contains_only_one_complete_scenario() -> None:
    assert list(DEMO_SCENARIOS) == [SCENARIO_NAME]


def test_demo_scenario_builder_produces_complete_inputs() -> None:
    position = build_demo_position(SCENARIO_NAME)
    profile, behavioural, debt = build_demo_case_data(SCENARIO_NAME)

    assert position.position_id == "01"
    assert profile is not None
    assert behavioural is not None
    assert debt is not None


def test_demo_scenario_covers_expected_triggered_rule_ids(assessment_service) -> None:
    case = _build_demo_case(assessment_service)
    assert _triggered_rule_ids(case) == EXPECTED_TRIGGERED_RULES


def test_demo_scenario_has_expected_final_status(assessment_service) -> None:
    case = _build_demo_case(assessment_service)
    assert case.final_assessment is not None
    assert case.final_assessment.status.value == EXPECTED_FINAL_STATUS


def test_demo_case_analysis_agent_preserves_final_assessment_status(
    assessment_service,
) -> None:
    case = _build_demo_case(assessment_service)
    analysis = CaseAnalysisAgent().run(case)
    assert analysis.assessment_status.value == EXPECTED_FINAL_STATUS


def test_ui_rule_evidence_source_covers_all_registered_demo_rules(
    assessment_service,
) -> None:
    """Ensure the Results-page evidence source exposes every deterministic rule ID."""
    case = _build_demo_case(assessment_service)
    result = SimpleNamespace(credit_case=case)
    displayed_rule_ids = {rule.rule_id for rule in get_rule_results(result)}

    assert displayed_rule_ids == EXPECTED_UI_RULE_IDS
