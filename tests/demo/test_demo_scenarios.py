import pytest

from app.demo_scenarios import DEMO_SCENARIOS, build_demo_case_data, build_demo_position
from app.workflow.assessment_workflow_factory import create_workflow
from src.rules.base.status import RuleStatus


EXPECTED_RULE_IDS = {
    "CP001",
    "CP002",
    "CP003",
    "R001",
    "R002",
    "R003",
    "R004",
    "R005",
    "R006",
    "R007",
    "B001",
    "B002",
    "B003",
    "B004",
    "DS001",
    "DS002",
    "DS003",
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
        if result.status == RuleStatus.TRIGGERED
    }
