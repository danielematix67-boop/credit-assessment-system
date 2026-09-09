import pytest

from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.report import Report


@pytest.fixture
def position_id():
    return "TEST_POSITION"


@pytest.fixture
def assessment_data(position_id):
    return {
        "position_id": position_id,
        "rule_results": [],
        "findings": [],
        "status": AssessmentStatus.CRITICAL,
    }


@pytest.fixture
def analysis_data(position_id):
    return {
        "position_id": position_id,
        "assessment_status": AssessmentStatus.CRITICAL,
        "key_findings": ["Test finding"],
        "risk_factors": ["Test risk factor"],
        "limitations": ["Test limitation"],
    }


@pytest.fixture
def report_data(position_id):
    return {
        "position_id": position_id,
        "assessment_status": AssessmentStatus.CRITICAL,
        "executive_summary": "Test executive summary.",
        "findings_by_category": {
            "test_category": ["Test finding"],
        },
        "limitations": ["Test limitation"],
    }


@pytest.fixture
def assessment(assessment_data):
    return Assessment(**assessment_data)


@pytest.fixture
def analysis(analysis_data):
    return AssessmentAnalysis(**analysis_data)


@pytest.fixture
def report(report_data):
    return Report(**report_data)


@pytest.fixture
def workflow_result(assessment, analysis, report):
    return AssessmentWorkflowResult(
        assessment=assessment,
        analysis=analysis,
        report=report,
    )


def test_assessment_workflow_result_preserves_components(
    workflow_result,
    assessment,
    analysis,
    report,
):
    assert workflow_result.assessment is assessment
    assert workflow_result.analysis is analysis
    assert workflow_result.report is report


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_assessment_workflow_result_accepts_all_assessment_statuses(
    position_id,
    status,
):
    assessment = Assessment(
        position_id=position_id,
        rule_results=[],
        findings=[],
        status=status,
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
        assessment=assessment,
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
        workflow_result.assessment = None

    with pytest.raises(AttributeError):
        workflow_result.analysis = None
