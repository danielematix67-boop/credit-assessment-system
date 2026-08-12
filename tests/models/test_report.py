import pytest

from src.models.assessment_status import AssessmentStatus
from src.models.report import Report


def test_report_can_be_created():
    report = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        executive_summary=(
            "The credit assessment is classified as critical."
        ),
        findings=[
            "Revenue growth deterioration",
            "Negative EBITDA",
        ],
        limitations=[
            "Interest coverage ratio was not evaluable",
        ],
    )

    assert report.position_id == "POS001"
    assert report.assessment_status == AssessmentStatus.CRITICAL
    assert report.executive_summary == (
        "The credit assessment is classified as critical."
    )
    assert report.findings == [
        "Revenue growth deterioration",
        "Negative EBITDA",
    ]
    assert report.limitations == [
        "Interest coverage ratio was not evaluable",
    ]


def test_report_is_immutable():
    report = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        executive_summary=(
            "The credit assessment is classified as critical."
        ),
        findings=[],
        limitations=[],
    )

    with pytest.raises(AttributeError):
        report.assessment_status = AssessmentStatus.NORMAL