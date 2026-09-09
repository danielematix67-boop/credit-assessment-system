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
    findings = [
        AnalysisFinding(
            rule_id=f"RULE_{index}",
            category=f"category_{index}",
            severity=severity,
            text=f"Finding {index}",
        )
        for index, severity in enumerate(
            [
                RuleSeverity.HIGH,
                RuleSeverity.MEDIUM,
                RuleSeverity.LOW,
            ],
            start=1,
        )
    ]

    return AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=next(iter(AssessmentStatus)),
        key_findings=findings,
        risk_factors=findings[:1],
        limitations=[
            AnalysisFinding(
                rule_id="LIMITATION",
                category="test_category",
                severity=RuleSeverity.LOW,
                text="Test limitation",
            ),
        ],
    )


@pytest.fixture
def generator():
    return MagicMock(spec=ReportGenerator)


# ============================================================
# Helpers
# ============================================================


def findings_by_category_from_analysis(
    analysis: AssessmentAnalysis,
) -> list[ReportFindingGroup]:
    categories: dict[str, list[AnalysisFinding]] = {}

    for finding in analysis.key_findings:
        categories.setdefault(
            finding.category,
            [],
        ).append(finding)

    return [
        ReportFindingGroup(
            category=category,
            findings=findings,
        )
        for category, findings in categories.items()
    ]


def build_report(
    analysis: AssessmentAnalysis,
    executive_summary: str = "Generated report",
) -> Report:
    return Report(
        position_id=analysis.position_id,
        assessment_status=analysis.assessment_status,
        executive_summary=executive_summary,
        findings_by_category=(findings_by_category_from_analysis(analysis)),
        limitations=analysis.limitations,
    )


def flatten_report_findings(
    report: Report,
) -> list[AnalysisFinding]:
    return [
        finding for group in report.findings_by_category for finding in group.findings
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


def test_reporting_agent_delegates_to_primary_generator(
    analysis,
    generator,
):
    expected_report = build_report(analysis)

    generator.generate.return_value = expected_report

    agent = ReportingAgent(generator)

    result = agent.run(analysis)

    assert result is expected_report
    generator.generate.assert_called_once_with(analysis)


def test_reporting_agent_preserves_report_content(
    analysis,
    generator,
):
    expected_report = build_report(analysis)

    generator.generate.return_value = expected_report

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == (analysis.assessment_status)

    assert flatten_report_findings(report) == analysis.key_findings

    assert report.limitations == analysis.limitations


# ============================================================
# Primary / fallback behaviour
# ============================================================


def test_reporting_agent_uses_fallback_when_primary_fails(
    analysis,
):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)

    expected_report = build_report(
        analysis,
        executive_summary="Fallback",
    )

    primary.generate.side_effect = RuntimeError()
    fallback.generate.return_value = expected_report

    agent = ReportingAgent(
        report_generator=primary,
        fallback_generator=fallback,
    )

    result = agent.run(analysis)

    assert result is expected_report

    primary.generate.assert_called_once_with(analysis)
    fallback.generate.assert_called_once_with(analysis)


def test_reporting_agent_does_not_use_fallback_when_primary_succeeds(
    analysis,
):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)

    expected_report = build_report(analysis)

    primary.generate.return_value = expected_report

    agent = ReportingAgent(
        report_generator=primary,
        fallback_generator=fallback,
    )

    result = agent.run(analysis)

    assert result is expected_report

    primary.generate.assert_called_once_with(analysis)
    fallback.generate.assert_not_called()


def test_reporting_agent_propagates_primary_error_without_fallback(
    analysis,
):
    generator = MagicMock(spec=ReportGenerator)

    error = RuntimeError("report generation failed")
    generator.generate.side_effect = error

    agent = ReportingAgent(generator)

    with pytest.raises(
        RuntimeError,
        match="report generation failed",
    ):
        agent.run(analysis)

    generator.generate.assert_called_once_with(analysis)


# ============================================================
# Fallback input contract
# ============================================================


def test_reporting_agent_passes_same_analysis_to_fallback(
    analysis,
):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)

    primary.generate.side_effect = RuntimeError()
    fallback.generate.return_value = build_report(analysis)

    agent = ReportingAgent(
        report_generator=primary,
        fallback_generator=fallback,
    )

    agent.run(analysis)

    passed_analysis = fallback.generate.call_args.args[0]

    assert passed_analysis is analysis


# ============================================================
# Assessment-status independence
# ============================================================


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_reporting_agent_supports_all_assessment_statuses(
    status,
    generator,
):
    analysis = AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=status,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    expected_report = build_report(analysis)

    generator.generate.return_value = expected_report

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert report.assessment_status == status
    assert report.position_id == analysis.position_id

    generator.generate.assert_called_once_with(analysis)


# ============================================================
# Content independence
# ============================================================


@pytest.mark.parametrize(
    "findings_count",
    [0, 1, 3, 5],
)
def test_reporting_agent_is_independent_of_number_of_findings(
    findings_count,
    generator,
):
    findings = [
        AnalysisFinding(
            rule_id=f"RULE_{index}",
            category=f"category_{index}",
            severity=RuleSeverity.MEDIUM,
            text=f"Finding {index}",
        )
        for index in range(findings_count)
    ]

    analysis = AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=next(iter(AssessmentStatus)),
        key_findings=findings,
        risk_factors=[],
        limitations=[],
    )

    expected_report = build_report(analysis)
    generator.generate.return_value = expected_report

    agent = ReportingAgent(generator)

    report = agent.run(analysis)

    assert flatten_report_findings(report) == findings

    assert report.limitations == analysis.limitations


# ============================================================
# Analysis immutability
# ============================================================


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


def test_reporting_agent_does_not_modify_analysis_on_fallback(
    analysis,
):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)

    original_key_findings = list(analysis.key_findings)
    original_risk_factors = list(analysis.risk_factors)
    original_limitations = list(analysis.limitations)

    primary.generate.side_effect = RuntimeError()
    fallback.generate.return_value = build_report(analysis)

    agent = ReportingAgent(
        report_generator=primary,
        fallback_generator=fallback,
    )

    agent.run(analysis)

    assert analysis.key_findings == original_key_findings
    assert analysis.risk_factors == original_risk_factors
    assert analysis.limitations == original_limitations


# ============================================================
# Runtime diagnostics
# ============================================================


def test_reporting_agent_records_primary_usage(
    analysis,
    generator,
):
    generator.generate.return_value = build_report(analysis)

    agent = ReportingAgent(generator)

    agent.run(analysis)

    assert agent.last_generator_used == "PRIMARY"
    assert agent.last_error is None


def test_reporting_agent_records_fallback_usage(
    analysis,
):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)

    primary.generate.side_effect = RuntimeError()
    fallback.generate.return_value = build_report(analysis)

    agent = ReportingAgent(
        report_generator=primary,
        fallback_generator=fallback,
    )

    agent.run(analysis)

    assert agent.last_generator_used == "FALLBACK"
    assert agent.last_error == "LLM report generation failed."


def test_reporting_agent_resets_diagnostics_after_success(
    analysis,
):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)

    primary.generate.side_effect = RuntimeError()
    fallback.generate.return_value = build_report(analysis)

    agent = ReportingAgent(
        report_generator=primary,
        fallback_generator=fallback,
    )

    agent.run(analysis)

    assert agent.last_generator_used == "FALLBACK"
    assert agent.last_error is not None

    primary.generate.side_effect = None
    primary.generate.return_value = build_report(analysis)

    agent.run(analysis)

    assert agent.last_generator_used == "PRIMARY"
    assert agent.last_error is None


# ============================================================
# Report generator implementation independence
# ============================================================


def test_reporting_agent_depends_only_on_report_generator_contract(
    analysis,
):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)

    expected_report = build_report(
        analysis,
        executive_summary="LLM-generated summary",
    )

    primary.generate.return_value = expected_report

    agent = ReportingAgent(
        report_generator=primary,
        fallback_generator=fallback,
    )

    report = agent.run(analysis)

    assert report.executive_summary == ("LLM-generated summary")

    primary.generate.assert_called_once_with(analysis)
    fallback.generate.assert_not_called()
