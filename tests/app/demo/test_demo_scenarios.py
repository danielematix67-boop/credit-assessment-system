from types import SimpleNamespace

from app.demo_scenarios import DEMO_SCENARIOS, build_demo_case_data, build_demo_position
from app.ui.results.helpers import get_rule_results
from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.services.credit_assessment_case_service import CreditAssessmentCaseService

SCENARIO_NAME = "01 · Complete Credit Assessment"
EXPECTED_FINAL_STATUS = "CRITICAL"

# Keep only representative scenario anchors here. Rule-specific tests cover
# individual trigger logic; this integration test should tolerate new rules.
CORE_TRIGGERED_RULES = {"CP001", "R002", "B001", "DS001"}

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
    assert profile.forborne is True


def test_demo_scenario_contains_core_triggers_and_covers_all_areas(
    assessment_service,
) -> None:
    case = _build_demo_case(assessment_service)
    triggered_rule_ids = _triggered_rule_ids(case)

    # Preserve a small set of representative critical signals without requiring
    # every new rule to be manually added to a fixed catalog.
    assert CORE_TRIGGERED_RULES <= triggered_rule_ids

    sections = (
        case.customer_profile,
        case.financial_analysis,
        case.behavioural_analysis,
        case.debt_sustainability,
    )
    assert all(any(result.is_triggered for result in section.evidence) for section in sections)


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


def test_ui_rule_evidence_source_covers_all_case_rules(
    assessment_service,
) -> None:
    """Ensure the Results-page evidence source exposes every case rule result."""
    case = _build_demo_case(assessment_service)
    result = SimpleNamespace(credit_case=case)

    expected_rule_ids = {
        rule.rule_id
        for section in (
            case.customer_profile,
            case.financial_analysis,
            case.behavioural_analysis,
            case.debt_sustainability,
        )
        for rule in section.evidence
    }
    displayed_rule_ids = {rule.rule_id for rule in get_rule_results(result)}

    assert displayed_rule_ids == expected_rule_ids
