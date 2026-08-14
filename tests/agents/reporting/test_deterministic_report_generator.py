import pytest

from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.report_generator import ReportGenerator
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus


@pytest.fixture
def generator():
    return DeterministicReportGenerator()


@pytest.fixture
def analysis():
    return AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=["Finding A", "Finding B"],
        risk_factors=["Risk A"],
        limitations=["Limitation A"],
    )


def test_deterministic_report_generator_implements_contract(generator):
    assert isinstance(generator, ReportGenerator)


def test_deterministic_report_generator_preserves_analysis_data(
    generator,
    analysis,
):
    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_deterministic_report_generator_generates_summary_for_each_status(
    generator,
    status,
):
    analysis = AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=status,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == status
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations
    assert report.executive_summary


def test_deterministic_report_generator_summary_depends_on_status(
    generator,
):
    summaries = {}

    for status in AssessmentStatus:
        analysis = AssessmentAnalysis(
            position_id="TEST_POSITION",
            assessment_status=status,
            key_findings=[],
            risk_factors=[],
            limitations=[],
        )

        report = generator.generate(analysis)
        summaries[status] = report.executive_summary

    assert len(set(summaries.values())) == len(AssessmentStatus)


def test_deterministic_report_generator_preserves_custom_content(
    generator,
):
    analysis = AssessmentAnalysis(
        position_id="CUSTOM_POSITION",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=["CUSTOM FINDING"],
        risk_factors=["CUSTOM RISK"],
        limitations=["CUSTOM LIMITATION"],
    )

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations