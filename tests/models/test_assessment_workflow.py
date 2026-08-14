import pytest

from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.report import Report


def test_assessment_workflow_result_can_be_created():
    assessment = Assessment(
        position_id="POS001",
        rule_results=[],
        findings=[],
        status=AssessmentStatus.CRITICAL,
    )

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=["Negative EBITDA"],
        risk_factors=["Negative EBITDA"],
        limitations=[],
    )

    report = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        executive_summary=(
            "The credit assessment is classified as critical."
        ),
        findings_by_category={
            "profitability": [
                "Negative EBITDA",
            ],
        },
        limitations=[],
    )

    result = AssessmentWorkflowResult(
        assessment=assessment,
        analysis=analysis,
        report=report,
    )

    assert result.assessment is assessment
    assert result.analysis is analysis
    assert result.report is report


def test_assessment_workflow_result_is_immutable():
    assessment = Assessment(
        position_id="POS001",
        rule_results=[],
        findings=[],
        status=AssessmentStatus.NORMAL,
    )

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.NORMAL,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    report = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.NORMAL,
        executive_summary=(
            "The credit assessment is classified as normal."
        ),
        findings_by_category={},
        limitations=[],
    )

    result = AssessmentWorkflowResult(
        assessment=assessment,
        analysis=analysis,
        report=report,
    )

    with pytest.raises(AttributeError):
        result.report = None