from unittest.mock import MagicMock

import pytest

from src.agents.base.agent import Agent
from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.report_generator import ReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.customer_profile_analysis import CustomerProfileAnalysis
from src.models.report import Report, ReportFindingGroup
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus

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


def test_llm_customer_profile_context_preserves_rewritten_rule_findings():
    finding = AnalysisFinding(
        rule_id="CP001",
        category="customer_profile",
        assessment_area="Customer Profile",
        severity=RuleSeverity.HIGH,
        text="Customer has an adverse risk signal.",
        status=RuleStatus.TRIGGERED,
        indicator="Adverse risk signal",
    )
    profile = CustomerProfileAnalysis(
        general_information="The company operates in manufacturing.",
        risk_profile="The current risk grade has deteriorated.",
    )
    analysis = AssessmentAnalysis(
        position_id="TEST_PROFILE",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[finding],
        risk_factors=[finding],
        limitations=[],
        rule_evidence=[finding],
        customer_profile=profile,
    )
    llm_narrative = (
        "Assessment Status: Critical\n\n"
        "**Customer Profile**\n\n"
        "The Adverse risk signal indicates a material customer-profile concern.\n\n"
        "**Financial Analysis**\n\n"
        "No anomalies were identified by the configured assessment rules.\n\n"
        "**Behavioural Analysis**\n\n"
        "No anomalies were identified by the configured assessment rules.\n\n"
        "**Debt Sustainability**\n\n"
        "No anomalies were identified by the configured assessment rules."
    )
    generator = LLMReportGenerator(llm_client=MagicMock())
    generator.generate = MagicMock(return_value=build_report(analysis, llm_narrative))

    report = ReportingAgent(generator).run(analysis)

    customer_section = report.executive_summary.split("**Financial Analysis**")[0]
    assert "The company operates in manufacturing." in customer_section
    assert "The current risk grade has deteriorated." in customer_section
    assert (
        "The Adverse risk signal indicates a material customer-profile concern."
        in customer_section
    )
    assert "Customer has an adverse risk signal." not in customer_section


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


def test_reporting_agent_propagates_fallback_error_when_primary_and_fallback_fail(
    analysis,
):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)

    primary_error = RuntimeError("primary generation failed")
    fallback_error = RuntimeError("fallback generation failed")
    primary.generate.side_effect = primary_error
    fallback.generate.side_effect = fallback_error

    agent = ReportingAgent(
        report_generator=primary,
        fallback_generator=fallback,
    )

    with pytest.raises(
        RuntimeError,
        match="fallback generation failed",
    ):
        agent.run(analysis)

    primary.generate.assert_called_once_with(analysis)
    fallback.generate.assert_called_once_with(analysis)
    assert agent.last_generator_used is None
    assert agent.last_error == "LLM report generation failed: primary generation failed"
    assert agent.last_error_category == "GENERATION_ERROR"


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
# Error classification
# ============================================================


class StatusCodeError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


@pytest.mark.parametrize(
    ("error", "expected_category"),
    [
        (StatusCodeError("quota exceeded", 429), "RATE_LIMIT"),
        (StatusCodeError("service unavailable", 503), "SERVICE_UNAVAILABLE"),
        (RuntimeError("connection refused"), "CONNECTION_ERROR"),
        (StatusCodeError("unauthorized", 401), "AUTHENTICATION"),
        (StatusCodeError("permission denied", 403), "AUTHORIZATION"),
        (RuntimeError("model not found"), "MODEL_UNAVAILABLE"),
        (TimeoutError("request timed out"), "TIMEOUT"),
        (RuntimeError("unexpected provider failure"), "GENERATION_ERROR"),
    ],
)
def test_reporting_agent_classifies_primary_errors(
    analysis,
    error,
    expected_category,
):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)
    primary.generate.side_effect = error
    fallback.generate.return_value = build_report(analysis)

    agent = ReportingAgent(
        report_generator=primary,
        fallback_generator=fallback,
    )

    agent.run(analysis)

    assert agent.last_generator_used == "FALLBACK"
    assert agent.last_error_category == expected_category
    assert agent.last_error


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


def test_reporting_agent_prefixes_cr_context_for_primary_report(analysis, generator):
    analysis = AssessmentAnalysis(
        position_id=analysis.position_id,
        assessment_status=analysis.assessment_status,
        key_findings=analysis.key_findings,
        risk_factors=analysis.risk_factors,
        limitations=analysis.limitations,
        behavioural_context={
            "cr_reference_date": "2026-09-30",
            "total_utilized_system": 1_250_000,
            "utilized_term": 800_000,
            "utilized_revocable": 150_000,
            "utilized_self_liquidating": 300_000,
        },
    )
    expected_report = build_report(
        analysis,
        executive_summary=(
            "Assessment Status: Attention\n\n"
            "**Customer Profile**\n\nCustomer context.\n\n"
            "**Financial Analysis**\n\nFinancial context.\n\n"
            "**Behavioural Analysis**\n\nBehavioural findings.\n\n"
            "**Debt Sustainability**\n\nDebt context."
        ),
    )
    generator.generate.return_value = expected_report

    report = ReportingAgent(generator).run(analysis)

    cr_comment = (
        "As of 30/09/2026, total system-wide utilised exposure amounted to "
        "approximately €1,250,000, comprising €800,000 in term facilities, "
        "€150,000 in revocable facilities and €300,000 in self-liquidating facilities."
    )
    assert cr_comment in report.executive_summary
    assert report.executive_summary.index(cr_comment) < report.executive_summary.index(
        "Behavioural findings."
    )
    assert report.executive_summary.count("Behavioural Analysis") == 1



def test_reporting_agent_uses_fixed_full_customer_profile_before_rule_findings(
    generator,
):
    analysis = AssessmentAnalysis(
        position_id="PROFILE_POSITION",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            AnalysisFinding(
                rule_id="CP_TEST",
                category="Customer Profile",
                severity=RuleSeverity.HIGH,
                text="Shareholder concentration exceeds the configured threshold",
                status=RuleStatus.TRIGGERED,
                assessment_area="Customer Profile",
                indicator="Shareholder concentration",
            )
        ],
        risk_factors=[],
        limitations=[],
        customer_profile=CustomerProfileAnalysis(
            general_information="Acme Manufacturing operates in the industrial sector.",
            risk_profile=(
                "The minimum regulatory risk grade is Past Due, compared with "
                "Bonis previously. Early-warning information includes an EWS "
                "score class of LIGHT_RED. The rating assessment records a rating "
                "of BB- and a probability of default (PD) of 0.18."
            ),
            relationship_context=(
                "The shareholders are Alpha (60%) and Beta (40%). Available credit "
                "facilities comprise a term loan of €500,000."
            ),
            relevant_events=(
                "The previous-restructuring status is yes. Forborne exposure is "
                "reported: yes. Recorded events include a historical restructuring."
            ),
        ),
    )
    generator.generate.return_value = build_report(
        analysis,
        executive_summary=(
            "Assessment Status: Attention\n\n"
            "**Customer Profile**\n\nLLM-generated profile that must be replaced.\n\n"
            "**Financial Analysis**\n\nFinancial findings.\n\n"
            "**Behavioural Analysis**\n\nBehavioural findings.\n\n"
            "**Debt Sustainability**\n\nDebt findings."
        ),
    )

    report = ReportingAgent(generator).run(analysis)
    summary = report.executive_summary

    assert "Acme Manufacturing operates in the industrial sector." in summary
    assert "The rating assessment records a rating of BB- and a probability of default (PD) of 0.18." in summary
    assert "minimum regulatory risk grade is Past Due" not in summary
    assert "LIGHT_RED" not in summary
    assert "previous-restructuring status" not in summary
    assert "Recorded events include" not in summary
    assert "The shareholders are Alpha (60%) and Beta (40%)." in summary
    assert "term loan of €500,000" in summary
    assert "LLM-generated profile" not in summary
    assert summary.index("Acme Manufacturing") < summary.index(
        "**Deterministic rule findings**"
    )
    assert summary.index("**Deterministic rule findings**") < summary.index(
        "Shareholder concentration exceeds the configured threshold"
    )
    assert summary.count("Customer Profile") == 1


def test_reporting_agent_adds_fixed_customer_profile_context_on_fallback(analysis):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)
    analysis = AssessmentAnalysis(
        position_id=analysis.position_id,
        assessment_status=analysis.assessment_status,
        key_findings=[],
        risk_factors=[],
        limitations=[],
        customer_profile=CustomerProfileAnalysis(
            general_information="Synthetic Industries operates in manufacturing.",
            risk_profile="The current regulatory risk grade is Bonis.",
        ),
    )
    primary.generate.side_effect = RuntimeError("provider unavailable")
    fallback.generate.return_value = build_report(
        analysis,
        executive_summary=(
            "Assessment Status: Normal\n\n"
            "### Customer Profile\n\nGenerated profile.\n\n"
            "### Financial Analysis\n\nNo anomalies.\n\n"
            "### Behavioural Analysis\n\nNo anomalies.\n\n"
            "### Debt Sustainability\n\nNo anomalies."
        ),
    )

    report = ReportingAgent(primary, fallback).run(analysis)

    assert "Synthetic Industries operates in manufacturing." in report.executive_summary
    assert "Generated profile." not in report.executive_summary

def test_reporting_agent_adds_cr_context_to_fallback_report(analysis):
    primary = MagicMock(spec=ReportGenerator)
    fallback = MagicMock(spec=ReportGenerator)
    analysis = AssessmentAnalysis(
        position_id=analysis.position_id,
        assessment_status=analysis.assessment_status,
        key_findings=analysis.key_findings,
        risk_factors=analysis.risk_factors,
        limitations=analysis.limitations,
        behavioural_context={
            "cr_reference_date": "2026-09-30",
            "total_utilized_system": 1_250_000,
            "utilized_term": 800_000,
            "utilized_revocable": 150_000,
            "utilized_self_liquidating": 300_000,
        },
    )
    primary.generate.side_effect = RuntimeError("provider unavailable")
    fallback.generate.return_value = build_report(
        analysis,
        executive_summary=(
            "Assessment Status: Attention\n\n"
            "### Customer Profile\n\nCustomer context.\n\n"
            "### Financial Analysis\n\nFinancial context.\n\n"
            "### Behavioural Analysis\n\nBehavioural findings.\n\n"
            "### Debt Sustainability\n\nDebt context."
        ),
    )

    report = ReportingAgent(primary, fallback).run(analysis)

    assert "As of 30/09/2026" in report.executive_summary
    assert report.executive_summary.index("As of 30/09/2026") < report.executive_summary.index(
        "Behavioural findings."
    )
