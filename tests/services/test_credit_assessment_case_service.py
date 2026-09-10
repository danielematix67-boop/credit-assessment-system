from unittest.mock import Mock

from src.models.assessment import Assessment
from src.models.assessment_status import AssessmentStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.position import CreditPosition
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
