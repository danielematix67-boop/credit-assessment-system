from unittest.mock import Mock

from src.models.assessment import Assessment
from src.models.assessment_section import SectionStatus
from src.models.assessment_status import AssessmentStatus
from src.models.behavioural_data import BehaviouralData
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.customer_profile_data import CustomerProfileData
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.position import CreditPosition
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.credit_assessment_case_service import CreditAssessmentCaseService


def _assessment(
    position: CreditPosition,
    status: AssessmentStatus = AssessmentStatus.NORMAL,
) -> Assessment:
    return Assessment(
        position_id=position.position_id,
        rule_results=[],
        findings=[],
        status=status,
    )


def test_case_service_builds_four_macro_sections_and_final_assessment() -> None:
    position = CreditPosition(position_id="TEST-001")
    assessment_service = Mock()
    assessment_service.assess.return_value = _assessment(position)
    case = CreditAssessmentCaseService(assessment_service).assess(position)

    assert isinstance(case, CreditAssessmentCase)
    assert [section.name for section in case.sections] == [
        "Customer Profile",
        "Financial Analysis",
        "Behavioural Analysis",
        "Debt Sustainability",
    ]
    assert case.financial_analysis.status == SectionStatus.NORMAL
    assert case.customer_profile.status == SectionStatus.NOT_EVALUABLE
    assert case.final_assessment is not None
    assert case.final_assessment.status == SectionStatus.ATTENTION


def test_case_service_preserves_financial_evidence() -> None:
    position = CreditPosition(position_id="TEST-002")
    assessment_service = Mock()
    assessment_service.assess.return_value = _assessment(
        position,
        AssessmentStatus.ATTENTION,
    )
    case = CreditAssessmentCaseService(assessment_service).assess(position)
    assert case.financial_analysis.evidence == []
    assert case.financial_analysis.status == SectionStatus.ATTENTION


def test_case_service_preserves_attention_for_all_not_evaluable_financial_rules() -> None:
    position = CreditPosition(position_id="TEST-002-NE")
    results = [
        RuleResult(
            rule_id=rule_id,
            rule_name=f"Rule {rule_id}",
            category="test",
            status=RuleStatus.NOT_EVALUABLE,
            value=None,
            threshold=0.0,
            severity=RuleSeverity.MEDIUM,
            indicator="Test indicator",
            direction=SeverityDirection.HIGHER_IS_WORSE,
        )
        for rule_id in ["R001", "R002", "R003", "R004", "R005", "R006", "R007"]
    ]
    assessment = Assessment(
        position_id=position.position_id,
        rule_results=results,
        findings=[],
        status=AssessmentStatus.ATTENTION,
    )
    assessment_service = Mock()
    assessment_service.assess.return_value = assessment

    case = CreditAssessmentCaseService(assessment_service).assess(position)

    assert case.financial_analysis.status == SectionStatus.ATTENTION
    assert case.financial_analysis.limitations == [
        "Financial indicators are not available for this case."
    ]


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
    results = [
        _rule_result(rule_id)
        for rule_id in ["R001", "R002", "R003", "R004", "R005", "R006", "R007"]
    ]
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


def test_case_service_builds_behavioural_section_when_data_are_available() -> None:
    position = CreditPosition(position_id="TEST-004")
    assessment_service = Mock()
    assessment_service.assess.return_value = _assessment(position)
    case = CreditAssessmentCaseService(assessment_service).assess(
        position,
        behavioural_data=BehaviouralData(average_utilization=0.95),
    )
    assert case.behavioural_analysis.status == SectionStatus.ATTENTION
    assert case.behavioural_analysis.evidence[0].rule_id == "B001"


def test_case_service_builds_debt_sustainability_section_when_data_are_available() -> None:
    position = CreditPosition(position_id="TEST-006")
    assessment_service = Mock()
    assessment_service.assess.return_value = _assessment(position)
    case = CreditAssessmentCaseService(assessment_service).assess(
        position,
        debt_sustainability_data=DebtSustainabilityData(
            cash_flow_available_for_debt_service=80,
            debt_service=100,
        ),
    )
    assert case.debt_sustainability.status == SectionStatus.ATTENTION
    assert len(case.debt_sustainability.evidence) == 3


def test_case_service_builds_customer_profile_when_data_are_available() -> None:
    position = CreditPosition(position_id="TEST-008")
    assessment_service = Mock()
    assessment_service.assess.return_value = _assessment(position)
    case = CreditAssessmentCaseService(assessment_service).assess(
        position,
        customer_profile_data=CustomerProfileData(
            company_name="Synthetic Co.",
            sector="Manufacturing",
        ),
    )
    assert case.customer_profile.status == SectionStatus.NORMAL
    assert case.customer_profile.context["company_name"] == "Synthetic Co."
