import pytest

from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.assessment_status import AssessmentStatus
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.final_assessment import FinalAssessment
from src.models.position import CreditPosition
from src.models.report import Report


@pytest.fixture
def position_id():
    return "TEST_POSITION"


@pytest.fixture
def case(position_id):
    section = AssessmentSection(
        name="Financial Analysis",
        status=SectionStatus.CRITICAL,
        findings=[],
        evidence=[],
        limitations=[],
    )
    return CreditAssessmentCase(
        position=CreditPosition(position_id=position_id),
        customer_profile=AssessmentSection(
            name="Customer Profile",
            status=SectionStatus.NORMAL,
            findings=[],
            evidence=[],
            limitations=[],
        ),
        financial_analysis=section,
        behavioural_analysis=AssessmentSection(
            name="Behavioural Analysis",
            status=SectionStatus.NORMAL,
            findings=[],
            evidence=[],
            limitations=[],
        ),
        debt_sustainability=AssessmentSection(
            name="Debt Sustainability",
            status=SectionStatus.NORMAL,
            findings=[],
            evidence=[],
            limitations=[],
        ),
        final_assessment=FinalAssessment(
            status=SectionStatus.CRITICAL,
            evaluated_sections=4,
        ),
    )


@pytest.fixture
def analysis(position_id):
    return AssessmentAnalysis(
        position_id=position_id,
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=["Test finding"],
        risk_factors=["Test risk factor"],
        limitations=["Test limitation"],
    )


@pytest.fixture
def report(position_id):
    return Report(
        position_id=position_id,
        assessment_status=AssessmentStatus.CRITICAL,
        executive_summary="Test executive summary.",
        findings_by_category={"test_category": ["Test finding"]},
        limitations=["Test limitation"],
    )


@pytest.fixture
def workflow_result(case, analysis, report):
    return AssessmentWorkflowResult(
        credit_case=case,
        analysis=analysis,
        report=report,
    )


def test_assessment_workflow_result_preserves_components(
    workflow_result,
    case,
    analysis,
    report,
):
    assert workflow_result.credit_case is case
    assert workflow_result.analysis is analysis
    assert workflow_result.report is report
    assert workflow_result.assessment.position_id == case.position.position_id


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_assessment_workflow_result_accepts_all_assessment_statuses(
    position_id,
    status,
):
    section_status = SectionStatus(status.value)
    case = CreditAssessmentCase(
        position=CreditPosition(position_id=position_id),
        customer_profile=AssessmentSection(
            name="Customer Profile",
            status=section_status,
            findings=[],
            evidence=[],
            limitations=[],
        ),
        financial_analysis=AssessmentSection(
            name="Financial Analysis",
            status=section_status,
            findings=[],
            evidence=[],
            limitations=[],
        ),
        behavioural_analysis=AssessmentSection(
            name="Behavioural Analysis",
            status=section_status,
            findings=[],
            evidence=[],
            limitations=[],
        ),
        debt_sustainability=AssessmentSection(
            name="Debt Sustainability",
            status=section_status,
            findings=[],
            evidence=[],
            limitations=[],
        ),
        final_assessment=FinalAssessment(
            status=section_status,
            evaluated_sections=4,
        ),
    )

    analysis = AssessmentAnalysis(
        position_id=position_id,
        assessment_status=status,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    report = Report(
        position_id=position_id,
        assessment_status=status,
        executive_summary="Test summary.",
        findings_by_category={},
        limitations=[],
    )

    result = AssessmentWorkflowResult(
        credit_case=case,
        analysis=analysis,
        report=report,
    )

    assert result.assessment.status == status
    assert result.analysis.assessment_status == status
    assert result.report.assessment_status == status


def test_assessment_workflow_result_is_immutable(
    workflow_result,
):
    with pytest.raises(AttributeError):
        workflow_result.report = None

    with pytest.raises(AttributeError):
        workflow_result.credit_case = None

    with pytest.raises(AttributeError):
        workflow_result.analysis = None
