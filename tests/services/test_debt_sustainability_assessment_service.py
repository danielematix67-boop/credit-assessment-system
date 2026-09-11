from pathlib import Path

from src.models.assessment_section import SectionStatus
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.rules.base.status import RuleStatus
from src.services.debt_sustainability_assessment_service import (
    DebtSustainabilityAssessmentService,
)


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


def test_dscr_is_evaluated_from_configured_inputs() -> None:
    section = DebtSustainabilityAssessmentService().assess(
        DebtSustainabilityData(cash_flow_available_for_debt_service=120, debt_service=100)
    )
    dscr = section.evidence[0]
    assert dscr.rule_id == "DS001"
    assert dscr.value == 1.2
    assert dscr.status == RuleStatus.NOT_TRIGGERED
    assert section.status == SectionStatus.NORMAL


def test_dscr_triggers_when_cash_flow_does_not_cover_debt_service() -> None:
    section = DebtSustainabilityAssessmentService().assess(
        DebtSustainabilityData(cash_flow_available_for_debt_service=80, debt_service=100)
    )
    assert section.evidence[0].status == RuleStatus.TRIGGERED
    assert section.status == SectionStatus.ATTENTION
    assert section.findings[0].comment.text.startswith("DSCR is 0.80x")


def test_debt_service_to_ebitda_triggers_above_configured_threshold() -> None:
    section = DebtSustainabilityAssessmentService().assess(
        DebtSustainabilityData(debt_service=130, ebitda=100)
    )
    result = section.evidence[1]
    assert result.rule_id == "DS002"
    assert result.value == 1.3
    assert result.status == RuleStatus.TRIGGERED


def test_cash_flow_buffer_triggers_when_negative() -> None:
    section = DebtSustainabilityAssessmentService().assess(
        DebtSustainabilityData(cash_flow_available_for_debt_service=90, debt_service=100)
    )
    result = section.evidence[2]
    assert result.rule_id == "DS003"
    assert result.value == -10
    assert result.status == RuleStatus.TRIGGERED


def test_dscr_and_buffer_do_not_double_count_one_cash_flow_weakness() -> None:
    section = DebtSustainabilityAssessmentService().assess(
        DebtSustainabilityData(cash_flow_available_for_debt_service=80, debt_service=100)
    )
    assert [result.rule_id for result in section.evidence if result.is_triggered] == ["DS001", "DS003"]
    assert section.status == SectionStatus.ATTENTION


def test_debt_service_and_cash_flow_weakness_is_critical_with_independent_burden() -> None:
    section = DebtSustainabilityAssessmentService().assess(
        DebtSustainabilityData(
            cash_flow_available_for_debt_service=80,
            debt_service=130,
            ebitda=100,
        )
    )
    assert section.status == SectionStatus.CRITICAL


def test_invalid_ratio_denominator_is_not_evaluable() -> None:
    section = DebtSustainabilityAssessmentService().assess(
        DebtSustainabilityData(cash_flow_available_for_debt_service=100, debt_service=0, ebitda=100)
    )
    assert section.evidence[0].status == RuleStatus.NOT_EVALUABLE


def test_all_debt_sustainability_indicators_not_evaluable() -> None:
    section = DebtSustainabilityAssessmentService().assess(DebtSustainabilityData())
    assert section.status == SectionStatus.ATTENTION
    assert all(result.status == RuleStatus.NOT_EVALUABLE for result in section.evidence)
    assert section.limitations == ["Debt-service and cash-flow data are not available."]


def test_debt_sustainability_does_not_depend_on_interest_expense() -> None:
    section = DebtSustainabilityAssessmentService().assess(
        DebtSustainabilityData(
            cash_flow_available_for_debt_service=120,
            debt_service=100,
            ebitda=100,
            interest_expense=20,
        )
    )
    assert [result.rule_id for result in section.evidence] == ["DS001", "DS002", "DS003"]
