from unittest.mock import MagicMock

import pytest

from src.agents.base.agent import Agent
from src.agents.reporting.report_generator import ReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report, ReportFindingGroup
from src.rules.base.severity import RuleSeverity


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def analysis():
    return AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            AnalysisFinding(
                rule_id="R001",
                category="revenue",
                severity=RuleSeverity.HIGH,
                text="Finding A",
            ),
            AnalysisFinding(
                rule_id="R002",
                category="profitability",
                severity=RuleSeverity.HIGH,
                text="Finding B",
            ),
        ],
        risk_factors=[
            AnalysisFinding(
                rule_id="R003",
                category="leverage",
                severity=RuleSeverity.MEDIUM,
                text="Risk A",
            ),
        ],
        limitations=[
            AnalysisFinding(
                rule_id="R004",
                category="data_quality",
                severity=RuleSeverity.LOW,
                text="Limitation A",
            ),
        ],
    )


@pytest.fixture
def generator():
    return MagicMock(spec=ReportGenerator)


# ============================================================
# Helpers
# ============================================================


def build_report(
    analysis,
    executive_summary="Generated report",
):
    """
    Build a deterministic Report from the supplied analysis.

    The helper mirrors the information-preservation contract
    expected from the ReportingAgent.
    """
    categories = {}

    for finding in analysis.key_findings:
        categories.setdefault(
            finding.category,
            [],
        ).append(finding)

    findings_by_category = [
        ReportFindingGroup(
            category=category,
            findings=findings,
        )
        for category, findings in categories.items()
    ]

    return Report(
        position_id=analysis.position_id,
        assessment_status=analysis.assessment_status,
        executive_summary=executive_summary,
        findings_by_category=findings_by_category,
        limitations=analysis.limitations,
    )


def flatten_report_findings(report):
    """Flatten report findings into a single list."""
    return [
        finding
        for group in report.findings_by_category
        for finding in group.findings
    ]


# ============================================================
# Agent contract
# ============================================================


def test_reporting_agent_implements_agent_contract(
    generator,
):
    agent = ReportingAgent(generator)

    assert isinstance(agent, Agent)


# ============================================================
# Primary generator
# ============================================================


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
    assert report.assessment_status == (
        analysis.assessment_status
    )

    assert (
        flatten_report_findings(report)
        == analysis.key_findings
    )

    assert report.limitations == analysis.limitations

    generator.generate.assert_called_once_with(analysis)


# ============================================================
# Fallback behaviour
# ============================================================


def test_reporting_agent_uses_fallback_when_primary_generator_fails(
    analysis,
):
    primary_generator = MagicMock(
        spec=ReportGenerator,
    )
    fallback_generator = MagicMock(
        spec=ReportGenerator,
    )

    expected_report = build_report(
        analysis,
        executive_summary="Deterministic fallback report",
    )

    primary_generator.generate.side_effect = RuntimeError(
        "LLM service unavailable"
    )

    fallback_generator.generate.return_value = (
        expected_report
    )

    agent = ReportingAgent(
        report_generator=primary_generator,
        fallback_generator=fallback_generator,
    )

    report = agent.run(analysis)

    assert report is expected_report

    primary_generator.generate.assert_called_once_with(
        analysis
    )

    fallback_generator.generate.assert_called_once_with(
        analysis
    )


def test_reporting_agent_fallback_preserves_analysis_content(
    analysis,
):
    primary_generator = MagicMock(
        spec=ReportGenerator,
    )
    fallback_generator = MagicMock(
        spec=ReportGenerator,
    )

    primary_generator.generate.side_effect = RuntimeError(
        "Gemini API unavailable"
    )

    fallback_report = build_report(
        analysis,
        executive_summary="Deterministic fallback report",
    )

    fallback_generator.generate.return_value = (
        fallback_report
    )

    agent = ReportingAgent(
        report_generator=primary_generator,
        fallback_generator=fallback_generator,
    )

    report = agent.run(analysis)

    assert report.position_id == analysis.position_id

    assert report.assessment_status == (
        analysis.assessment_status
    )

    assert (
        flatten_report_findings(report)
        == analysis.key_findings
    )

    assert report.limitations == analysis.limitations


def test_reporting_agent_passes_same_analysis_to_fallback(
    analysis,
):
    primary_generator = MagicMock(
        spec=ReportGenerator,
    )
    fallback_generator = MagicMock(
        spec=ReportGenerator,
    )

    primary_generator.generate.side_effect = RuntimeError(
        "Primary generator failed"
    )

    fallback_generator.generate.return_value = (
        build_report(analysis)
    )

    agent = ReportingAgent(
        report_generator=primary_generator,
        fallback_generator=fallback_generator,
    )

    agent.run(analysis)

    fallback_generator.generate.assert_called_once_with(
        analysis
    )

    passed_analysis = (
        fallback_generator.generate.call_args.args[0]
    )

    assert passed_analysis is analysis


def test_reporting_agent_does_not_call_fallback_when_primary_succeeds(
    analysis,
):
    primary_generator = MagicMock(
        spec=ReportGenerator,
    )
    fallback_generator = MagicMock(
        spec=ReportGenerator,
    )

    expected_report = build_report(analysis)

    primary_generator.generate.return_value = (
        expected_report
    )

    agent = ReportingAgent(
        report_generator=primary_generator,
        fallback_generator=fallback_generator,
    )

    report = agent.run(analysis)

    assert report is expected_report

    primary_generator.generate.assert_called_once_with(
        analysis
    )

    fallback_generator.generate.assert_not_called()


# ============================================================
# Failure without fallback
# ============================================================


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

    generator.generate.assert_called_once_with(
        analysis
    )


# ============================================================
# Analysis immutability
# ============================================================


def test_reporting_agent_does_not_modify_analysis(
    analysis,
    generator,
):
    original_key_findings = list(
        analysis.key_findings
    )

    original_risk_factors = list(
        analysis.risk_factors
    )

    original_limitations = list(
        analysis.limitations
    )

    generator.generate.return_value = (
        build_report(analysis)
    )

    agent = ReportingAgent(generator)

    agent.run(analysis)

    assert (
        analysis.key_findings
        == original_key_findings
    )

    assert (
        analysis.risk_factors
        == original_risk_factors
    )

    assert (
        analysis.limitations
        == original_limitations
    )


def test_reporting_agent_does_not_modify_analysis_on_fallback(
    analysis,
):
    primary_generator = MagicMock(
        spec=ReportGenerator,
    )
    fallback_generator = MagicMock(
        spec=ReportGenerator,
    )

    original_key_findings = list(
        analysis.key_findings
    )

    original_risk_factors = list(
        analysis.risk_factors
    )

    original_limitations = list(
        analysis.limitations
    )

    primary_generator.generate.side_effect = RuntimeError(
        "LLM unavailable"
    )

    fallback_generator.generate.return_value = (
        build_report(analysis)
    )

    agent = ReportingAgent(
        report_generator=primary_generator,
        fallback_generator=fallback_generator,
    )

    agent.run(analysis)

    assert (
        analysis.key_findings
        == original_key_findings
    )

    assert (
        analysis.risk_factors
        == original_risk_factors
    )

    assert (
        analysis.limitations
        == original_limitations
    )


# ============================================================
# Content independence
# ============================================================


@pytest.mark.parametrize(
    (
        "key_findings",
        "risk_factors",
        "limitations",
    ),
    [
        (
            [
                AnalysisFinding(
                    rule_id="R001",
                    category="revenue",
                    severity=RuleSeverity.HIGH,
                    text="Finding A",
                ),
            ],
            [
                AnalysisFinding(
                    rule_id="R002",
                    category="leverage",
                    severity=RuleSeverity.MEDIUM,
                    text="Risk A",
                ),
            ],
            [
                AnalysisFinding(
                    rule_id="R003",
                    category="data_quality",
                    severity=RuleSeverity.LOW,
                    text="Limitation A",
                ),
            ],
        ),
        (
            [
                AnalysisFinding(
                    rule_id="R001",
                    category="profitability",
                    severity=RuleSeverity.HIGH,
                    text="Custom finding",
                ),
            ],
            [
                AnalysisFinding(
                    rule_id="R002",
                    category="leverage",
                    severity=RuleSeverity.MEDIUM,
                    text="Custom risk",
                ),
            ],
            [
                AnalysisFinding(
                    rule_id="R003",
                    category="data_quality",
                    severity=RuleSeverity.LOW,
                    text="Custom limitation",
                ),
            ],
        ),
        (
            [],
            [],
            [],
        ),
        (
            [
                AnalysisFinding(
                    rule_id="R001",
                    category="revenue",
                    severity=RuleSeverity.HIGH,
                    text="Finding A",
                ),
                AnalysisFinding(
                    rule_id="R002",
                    category="profitability",
                    severity=RuleSeverity.HIGH,
                    text="Finding B",
                ),
                AnalysisFinding(
                    rule_id="R003",
                    category="leverage",
                    severity=RuleSeverity.MEDIUM,
                    text="Finding C",
                ),
            ],
            [
                AnalysisFinding(
                    rule_id="R004",
                    category="leverage",
                    severity=RuleSeverity.MEDIUM,
                    text="Risk A",
                ),
                AnalysisFinding(
                    rule_id="R005",
                    category="liquidity",
                    severity=RuleSeverity.MEDIUM,
                    text="Risk B",
                ),
            ],
            [
                AnalysisFinding(
                    rule_id="R006",
                    category="data_quality",
                    severity=RuleSeverity.LOW,
                    text="Limitation A",
                ),
                AnalysisFinding(
                    rule_id="R007",
                    category="data_quality",
                    severity=RuleSeverity.LOW,
                    text="Limitation B",
                ),
            ],
        ),
    ],
)
def test_reporting_agent_is_independent_of_analysis_content(
    key_findings,
    risk_factors,
    limitations,
    generator,
):
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=key_findings,
        risk_factors=risk_factors,
        limitations=limitations,
    )

    generator.generate.return_value = (
        build_report(analysis)
    )

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert (
        flatten_report_findings(report)
        == key_findings
    )

    assert report.limitations == limitations

    generator.generate.assert_called_once_with(
        analysis
    )
