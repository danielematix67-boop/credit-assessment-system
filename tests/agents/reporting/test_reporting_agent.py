from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
import pytest


def test_reporting_agent_generates_report_from_analysis():

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

    agent = ReportingAgent()

    report = agent.run(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations

@pytest.mark.parametrize(
    "status, expected_summary",
    [
        (
            AssessmentStatus.NORMAL,
            "The credit assessment is classified as normal.",
        ),
        (
            AssessmentStatus.ATTENTION,
            "The credit assessment requires attention.",
        ),
        (
            AssessmentStatus.CRITICAL,
            "The credit assessment is classified as critical.",
        ),
    ],
)
def test_reporting_agent_generates_summary_from_status(
    status,
    expected_summary,
):

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=status,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    report = ReportingAgent().run(analysis)

    assert report.executive_summary == expected_summary

def test_reporting_agent_does_not_depend_on_rule_ids():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            "Custom Revenue Indicator",
            "Custom Leverage Indicator",
        ],
        risk_factors=[],
        limitations=[],
    )

    report = ReportingAgent().run(analysis)

    assert report.findings == [
        "Custom Revenue Indicator",
        "Custom Leverage Indicator",
    ]