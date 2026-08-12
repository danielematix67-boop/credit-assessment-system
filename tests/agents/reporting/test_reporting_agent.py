from unittest.mock import MagicMock

from src.agents.base.agent import Agent
from src.agents.reporting.report_generator import ReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)

def test_reporting_agent_implements_agent_contract():

    generator = MagicMock(spec=ReportGenerator)

    agent = ReportingAgent(generator)

    assert isinstance(agent, Agent)


def test_reporting_agent_delegates_report_generation():

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

    expected_report = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        executive_summary="Generated report",
        findings=analysis.key_findings,
        limitations=analysis.limitations,
    )

    generator = MagicMock(spec=ReportGenerator)
    generator.generate.return_value = expected_report

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert report is expected_report

    generator.generate.assert_called_once_with(analysis)


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

    expected_report = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        executive_summary="Generated report",
        findings=[
            "Custom Revenue Indicator",
            "Custom Leverage Indicator",
        ],
        limitations=[],
    )

    generator = MagicMock(spec=ReportGenerator)
    generator.generate.return_value = expected_report

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert report.findings == [
        "Custom Revenue Indicator",
        "Custom Leverage Indicator",
    ]

    generator.generate.assert_called_once_with(analysis)