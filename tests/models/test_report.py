import pytest

from src.models.assessment_status import AssessmentStatus
from src.models.report import Report


@pytest.fixture
def report_data():
    return {
        "position_id": "TEST_POSITION",
        "assessment_status": AssessmentStatus.CRITICAL,
        "executive_summary": (
            "The credit assessment is classified as critical."
        ),
        "findings_by_category": {
            "revenue": [
                "Revenue growth deterioration",
            ],
            "profitability": [
                "Negative EBITDA",
            ],
        },
        "limitations": [
            "Interest coverage ratio was not evaluable",
        ],
    }


@pytest.fixture
def report(report_data):
    return Report(**report_data)


def test_report_preserves_provided_data(
    report,
    report_data,
):
    for field_name, expected_value in report_data.items():
        assert getattr(report, field_name) == expected_value


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_report_accepts_valid_assessment_status(
    report_data,
    status,
):
    data = {
        **report_data,
        "assessment_status": status,
    }

    report = Report(**data)

    assert report.assessment_status == status


def test_report_is_immutable(report):
    with pytest.raises(AttributeError):
        report.assessment_status = None