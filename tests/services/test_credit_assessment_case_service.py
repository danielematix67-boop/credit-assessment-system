from unittest.mock import Mock

from src.models.assessment import Assessment
from src.models.assessment_status import AssessmentStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.position import CreditPosition
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.credit_assessment_case_service import CreditAssessmentCaseService


def test_case_service_builds_four_macro_sections() -> None:
    position = CreditPosition(position_id="TEST-001")
    assessment = Assessment(
        position_id=position.position_id,
        rule_results=[],
        findings=[],
        status=AssessmentStatus.NORMAL,
    )

    assessment_service = Mock()
    assessment_service.assess.return_value = assessment

    case = CreditAssessmentCaseService(assessment_service).assess(position)

    assert isinstance(case, CreditAssessmentCase)
    assert [section.name for section in case.sections] == [
        "Customer Profile",
        "Financial Analysis",
        "Behavioural Analysis",
        "Debt Sustainability",
    ]
    assert case.financial_analysis.status.value == "NORMAL"
    assert case.customer_profile.status.value == "NOT_EVALUABLE"
    assert case.behavioural_analysis.status.value == "NOT_EVALUABLE"
    assert case.debt_sustainability.status.value == "NOT_EVALUABLE"


def test_case_service_preserves_financial_evidence() -> None:
    position = CreditPosition(position_id="TEST-002")
    assessment = Assessment(
        position_id=position.position_id,
        rule_results=[],
        findings=[],
        status=AssessmentStatus.ATTENTION,
    )

    assessment_service = Mock()
    assessment_service.assess.return_value = assessment

    case = CreditAssessmentCaseService(assessment_service).assess(position)

    assert case.financial_analysis.findings == assessment.findings
    assert case.financial_analysis.evidence == assessment.rule_results
    assert case.financial_analysis.limitations == []


def _rule_result(rule_id: str) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=f"Rule {rule_id}",
        category="test",
        status=RuleStatus.NOT_TRIGGERED,
        value=1.0,
        threshold=2.0,
        severity=RuleSeverity.MEDIUM,
        indicator="Test indicator",
        direction=SeverityDirection.HIGHER_IS_WORSE,
    )


def test_case_service_groups_financial_rules_by_analyst_dimension() -> None:
    position = CreditPosition(position_id="TEST-003")
    results = [_rule_result(rule_id) for rule_id in ["R001", "R002", "R003", "R004", "R005", "R006", "R007"]]
    assessment = Assessment(
        position_id=position.position_id,
        rule_results=results,
        findings=[],
        status=AssessmentStatus.NORMAL,
    )

    assessment_service = Mock()
    assessment_service.assess.return_value = assessment

    case = CreditAssessmentCaseService(assessment_service).assess(position)
    dimensions = case.financial_analysis.dimensions

    assert list(dimensions) == [
        "Revenue & Growth",
        "Profitability",
        "Financial Structure",
        "Debt Service Burden",
        "Profitability Quality",
    ]
    assert [result.rule_id for result in dimensions["Revenue & Growth"]] == ["R001"]
    assert [result.rule_id for result in dimensions["Profitability"]] == ["R002", "R003"]
    assert [result.rule_id for result in dimensions["Financial Structure"]] == ["R004"]
    assert [result.rule_id for result in dimensions["Debt Service Burden"]] == ["R005", "R007"]
    assert [result.rule_id for result in dimensions["Profitability Quality"]] == ["R006"]
