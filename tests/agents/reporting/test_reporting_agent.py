from unittest.mock import MagicMock

import pytest

from src.agents.base.agent import Agent
from src.agents.reporting.report_generator import ReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report


def test_reporting_agent_implements_agent_contract():

    generator = MagicMock(spec=ReportGenerator)

    agent = ReportingAgent(generator)

    assert isinstance(agent, Agent)


def test_reporting_agent_delegates_report_generation():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue deterioration detected.",
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "Negative EBITDA detected.",
        ],
        limitations=[
            "EBITDA Inventory Contribution could not be evaluated.",
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


def test_reporting_agent_preserves_analysis_content():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            "Revenue deterioration detected.",
            "High leverage detected.",
        ],
        risk_factors=[
            "High leverage detected.",
        ],
        limitations=[
            "Interest Coverage Ratio could not be evaluated.",
        ],
    )

    expected_report = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        executive_summary="Generated report",
        findings=analysis.key_findings,
        limitations=analysis.limitations,
    )

    generator = MagicMock(spec=ReportGenerator)
    generator.generate.return_value = expected_report

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations

    generator.generate.assert_called_once_with(analysis)


def test_reporting_agent_uses_fallback_when_primary_generator_fails():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue deterioration detected.",
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "Negative EBITDA detected.",
        ],
        limitations=[
            "Interest Coverage Ratio could not be evaluated.",
        ],
    )

    primary_generator = MagicMock(spec=ReportGenerator)
    fallback_generator = MagicMock(spec=ReportGenerator)

    expected_report = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        executive_summary="Deterministic fallback report",
        findings=analysis.key_findings,
        limitations=analysis.limitations,
    )

    primary_generator.generate.side_effect = RuntimeError(
        "LLM service unavailable"
    )

    fallback_generator.generate.return_value = expected_report

    agent = ReportingAgent(
        report_generator=primary_generator,
        fallback_generator=fallback_generator,
    )

    report = agent.run(analysis)

    assert report is expected_report

    primary_generator.generate.assert_called_once_with(analysis)
    fallback_generator.generate.assert_called_once_with(analysis)


def test_reporting_agent_raises_when_primary_fails_without_fallback():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "Negative EBITDA detected.",
        ],
        limitations=[],
    )

    generator = MagicMock(spec=ReportGenerator)

    generator.generate.side_effect = RuntimeError(
        "Report generation failed"
    )

    agent = ReportingAgent(generator)

    with pytest.raises(
        RuntimeError,
        match="Report generation failed",
    ):
        agent.run(analysis)

    generator.generate.assert_called_once_with(analysis)


def test_reporting_agent_passes_same_analysis_to_fallback():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            "Revenue deterioration detected.",
        ],
        risk_factors=[
            "Revenue deterioration detected.",
        ],
        limitations=[
            "Interest Coverage Ratio could not be evaluated.",
        ],
    )

    primary_generator = MagicMock(spec=ReportGenerator)
    fallback_generator = MagicMock(spec=ReportGenerator)

    primary_generator.generate.side_effect = RuntimeError(
        "Primary generator failed"
    )

    fallback_generator.generate.return_value = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        executive_summary="Fallback report",
        findings=analysis.key_findings,
        limitations=analysis.limitations,
    )

    agent = ReportingAgent(
        report_generator=primary_generator,
        fallback_generator=fallback_generator,
    )

    agent.run(analysis)

    fallback_generator.generate.assert_called_once_with(analysis)

    passed_analysis = fallback_generator.generate.call_args.args[0]

    assert passed_analysis is analysis


def test_reporting_agent_does_not_modify_analysis():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue deterioration detected.",
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "Negative EBITDA detected.",
        ],
        limitations=[
            "Interest Coverage Ratio could not be evaluated.",
        ],
    )

    original_key_findings = list(analysis.key_findings)
    original_risk_factors = list(analysis.risk_factors)
    original_limitations = list(analysis.limitations)

    generator = MagicMock(spec=ReportGenerator)

    generator.generate.return_value = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        executive_summary="Generated report",
        findings=analysis.key_findings,
        limitations=analysis.limitations,
    )

    agent = ReportingAgent(generator)

    agent.run(analysis)

    assert analysis.key_findings == original_key_findings
    assert analysis.risk_factors == original_risk_factors
    assert analysis.limitations == original_limitations


def test_reporting_agent_is_independent_of_rule_ids():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            "Custom business comment.",
        ],
        risk_factors=[
            "Custom business comment.",
        ],
        limitations=[
            "Custom limitation comment.",
        ],
    )

    expected_report = Report(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        executive_summary="Generated report",
        findings=analysis.key_findings,
        limitations=analysis.limitations,
    )

    generator = MagicMock(spec=ReportGenerator)
    generator.generate.return_value = expected_report

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert report.findings == [
        "Custom business comment.",
    ]

    assert report.limitations == [
        "Custom limitation comment.",
    ]

    generator.generate.assert_called_once_with(analysis)