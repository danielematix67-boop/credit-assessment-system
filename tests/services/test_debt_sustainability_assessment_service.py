from pathlib import Path

from src.models.assessment_section import SectionStatus
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.rules.base.status import RuleStatus
from src.services.debt_sustainability_assessment_service import DebtSustainabilityAssessmentService


CONFIG_PATH = Path("config/debt_sustainability_rules.yaml")


def test_debt_sustainability_loads_all_configured_rules() -> None:
    section = DebtSustainabilityAssessmentService().assess(
        DebtSustainabilityData(
            cash_flow_available_for_debt_service=120,
            debt_service=100,
            ebitda=100,
        )
    )
    assert [result.rule_id for result in section.evidence] == ["DS001", "DS002", "DS003"]
    assert all(result.comment_template for result in section.evidence)
