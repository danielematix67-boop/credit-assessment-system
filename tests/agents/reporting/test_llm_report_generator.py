from unittest.mock import Mock

import pytest

from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus


def make_finding(
    text: str,
    category: str = "Revenue",
) -> AnalysisFinding:
    return AnalysisFinding(
        rule_id="R001",
        category=category,
        severity=RuleSeverity.HIGH,
        text=text,
        status=RuleStatus.TRIGGERED,
    )


def make_analysis(
    *,
    status: AssessmentStatus = AssessmentStatus.CRITICAL,
    key_findings: list[AnalysisFinding] | None = None,
) -> AssessmentAnalysis:
    findings = key_findings or []
    return AssessmentAnalysis(
        position_id="TEST-001",
        assessment_status=status,
        key_findings=findings,
        risk_factors=findings,
        limitations=[],
    )


def make_generator(
    *,
    response: str,
    require_indicator_values: bool = False,
) -> tuple[LLMReportGenerator, Mock]:
    client = Mock()
    client.generate.return_value = response
    return (
        LLMReportGenerator(
            client,
            require_indicator_values=require_indicator_values,
        ),
        client,
    )


def test_indicator_grounding_allows_omitted_source_indicators() -> None:
    findings = [
        make_finding("Revenue growth declined to -20.0%.", category="Revenue"),
        make_finding(
            "EBITDA is negative at €-120,000.",
            category="Profitability",
        ),
        make_finding(
            "NFP to EBITDA stands at 7.0x.",
            category="Leverage",
        ),
    ]
    analysis = make_analysis(
        status=AssessmentStatus.CRITICAL,
        key_findings=findings,
    )
    response = "EBITDA is negative and leverage remains elevated."
    generator, _ = make_generator(
        response=response,
        require_indicator_values=True,
    )

    report = generator.generate(analysis)

    assert report.executive_summary == "Assessment Status: Critical\n\n" + response


def test_indicator_grounding_accepts_equivalent_numeric_formatting() -> None:
    findings = [
        make_finding("Revenue growth declined to -20.0%.", category="Revenue"),
        make_finding("NFP to EBITDA stands at 7.0x.", category="Leverage"),
    ]
    response = "Revenue growth declined to -20% and NFP to EBITDA stands at 7x."
    generator, _ = make_generator(
        response=response,
        require_indicator_values=True,
    )

    report = generator.generate(make_analysis(key_findings=findings))

    assert report.executive_summary.endswith(response)


def test_indicator_grounding_accepts_decimal_comma_formatting() -> None:
    findings = [
        make_finding("Revenue growth declined to -20.0%.", category="Revenue"),
    ]
    response = "Revenue growth declined to -20,0%."
    generator, _ = make_generator(
        response=response,
        require_indicator_values=True,
    )

    report = generator.generate(make_analysis(key_findings=findings))

    assert report.executive_summary.endswith(response)


def test_indicator_grounding_sanitizes_unsupported_numeric_values() -> None:
    findings = [
        make_finding("Revenue growth declined to -20.0%.", category="Revenue"),
    ]
    generator, _ = make_generator(
        response=(
            "Revenue growth declined to -35%. "
            "The overall financial profile remains under pressure."
        ),
        require_indicator_values=True,
    )

    report = generator.generate(make_analysis(key_findings=findings))

    assert "-35%" not in report.executive_summary
    assert "overall financial profile remains under pressure" in report.executive_summary


def test_indicator_grounding_accepts_all_present_values() -> None:
    findings = [
        make_finding("Revenue growth declined to 20.0%.", category="Revenue"),
        make_finding("NFP to EBITDA stands at 7.0x.", category="Leverage"),
    ]
    response = (
        "Revenue growth declined to 20.0% and "
        "NFP to EBITDA stands at 7.0x."
    )
    generator, _ = make_generator(
        response=response,
        require_indicator_values=True,
    )

    report = generator.generate(make_analysis(key_findings=findings))

    assert report.executive_summary.endswith(response)

