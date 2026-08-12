from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.report_generator import ReportGenerator
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus


def test_deterministic_report_generator_implements_contract():

    generator = DeterministicReportGenerator()

    assert isinstance(generator, ReportGenerator)


def test_deterministic_report_generator_generates_report():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue Growth Deterioration",
            "Negative EBITDA",
        ],
        risk_factors=[
            "High leverage",
        ],
        limitations=[
            "Interest Coverage Ratio",
        ],
    )

    generator = DeterministicReportGenerator()

    report = generator.generate(analysis)

    assert report.position_id == "POS001"
    assert report.assessment_status == AssessmentStatus.CRITICAL

    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations

    assert report.executive_summary == (
        "The credit assessment is classified as critical."
    )


def test_deterministic_report_generator_generates_normal_summary():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.NORMAL,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    report = DeterministicReportGenerator().generate(analysis)

    assert report.executive_summary == (
        "The credit assessment is classified as normal."
    )


def test_deterministic_report_generator_generates_attention_summary():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=["High leverage"],
        risk_factors=["High leverage"],
        limitations=[],
    )

    report = DeterministicReportGenerator().generate(analysis)

    assert report.executive_summary == (
        "The credit assessment requires attention."
    )