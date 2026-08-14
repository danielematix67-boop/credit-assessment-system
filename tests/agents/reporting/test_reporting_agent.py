from unittest.mock import MagicMock

import pytest

from src.agents.base.agent import Agent
from src.agents.reporting.report_generator import ReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report


@pytest.fixture
def analysis():
    return AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Finding A",
            "Finding B",
        ],
        risk_factors=[
            "Risk A",
        ],
        limitations=[
            "Limitation A",
        ],
    )


@pytest.fixture
def generator():
    return MagicMock(spec=ReportGenerator)


def build_report(
    analysis,
    executive_summary="Generated report",
):
    return Report(
        position_id=analysis.position_id,
        assessment_status=analysis.assessment_status,
        executive_summary=executive_summary,
        findings=analysis.key_findings,
        limitations=analysis.limitations,
    )


def test_reporting_agent_implements_agent_contract(generator):
    agent = ReportingAgent(generator)

    assert isinstance(agent, Agent)


def test_reporting_agent_delegates_report_generation(
    analysis,
    generator,
):
    expected_report = build_report(analysis)

    generator.generate.return_value = expected_report

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert report is expected_report
    generator.generate.assert_called_once_with(analysis)


def test_reporting_agent_preserves_analysis_content(
    analysis,
    generator,
):
    expected_report = build_report(analysis)

    generator.generate.return_value = expected_report

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations

    generator.generate.assert_called_once_with(analysis)


def test_reporting_agent_uses_fallback_when_primary_generator_fails(
    analysis,
):
    primary_generator = MagicMock(spec=ReportGenerator)
    fallback_generator = MagicMock(spec=ReportGenerator)

    expected_report = build_report(
        analysis,
        executive_summary="Deterministic fallback report",
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


def test_reporting_agent_raises_when_primary_fails_without_fallback(
    analysis,
    generator,
):
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


def test_reporting_agent_passes_same_analysis_to_fallback(
    analysis,
):
    primary_generator = MagicMock(spec=ReportGenerator)
    fallback_generator = MagicMock(spec=ReportGenerator)

    primary_generator.generate.side_effect = RuntimeError(
        "Primary generator failed"
    )

    fallback_generator.generate.return_value = build_report(analysis)

    agent = ReportingAgent(
        report_generator=primary_generator,
        fallback_generator=fallback_generator,
    )

    agent.run(analysis)

    fallback_generator.generate.assert_called_once_with(analysis)

    passed_analysis = fallback_generator.generate.call_args.args[0]

    assert passed_analysis is analysis


def test_reporting_agent_does_not_modify_analysis(
    analysis,
    generator,
):
    original_key_findings = list(analysis.key_findings)
    original_risk_factors = list(analysis.risk_factors)
    original_limitations = list(analysis.limitations)

    generator.generate.return_value = build_report(analysis)

    agent = ReportingAgent(generator)

    agent.run(analysis)

    assert analysis.key_findings == original_key_findings
    assert analysis.risk_factors == original_risk_factors
    assert analysis.limitations == original_limitations


@pytest.mark.parametrize(
    (
        "key_findings",
        "risk_factors",
        "limitations",
        "expected_findings",
        "expected_limitations",
    ),
    [
        (
            ["Finding A"],
            ["Risk A"],
            ["Limitation A"],
            ["Finding A"],
            ["Limitation A"],
        ),
        (
            ["Custom finding"],
            ["Custom risk"],
            ["Custom limitation"],
            ["Custom finding"],
            ["Custom limitation"],
        ),
        (
            [],
            [],
            [],
            [],
            [],
        ),
        (
            ["Finding A", "Finding B", "Finding C"],
            ["Risk A", "Risk B"],
            ["Limitation A", "Limitation B"],
            ["Finding A", "Finding B", "Finding C"],
            ["Limitation A", "Limitation B"],
        ),
    ],
)
def test_reporting_agent_is_independent_of_analysis_content(
    key_findings,
    risk_factors,
    limitations,
    expected_findings,
    expected_limitations,
    generator,
):
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=key_findings,
        risk_factors=risk_factors,
        limitations=limitations,
    )

    generator.generate.return_value = build_report(analysis)

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert report.findings == expected_findings
    assert report.limitations == expected_limitations

    generator.generate.assert_called_once_with(analysis)