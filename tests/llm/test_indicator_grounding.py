from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.llm.mock_client import MockLLMClient
from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.rules.base.severity import RuleSeverity


def make_analysis(*findings: AnalysisFinding) -> AssessmentAnalysis:
    return AssessmentAnalysis(
        position_id="TEST-INDICATORS",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=list(findings),
        risk_factors=list(findings),
        limitations=[],
    )


def make_finding(text: str) -> AnalysisFinding:
    return AnalysisFinding(
        rule_id="R001",
        category="Financial Risk",
        severity=RuleSeverity.HIGH,
        text=text,
    )


def test_prompt_explicitly_requires_indicator_values() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to 20.0%."),
    )

    prompt = ReportPromptBuilder().build(analysis)

    assert "Every numerical indicator value" in prompt
    assert "must be explicitly reported in the narrative" in prompt
    assert "Do not round, recalculate, convert or replace" in prompt


def test_local_llm_report_appends_missing_indicator_values() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to 20.0%."),
        make_finding("EBITDA is negative at €-120,000."),
        make_finding("NFP to EBITDA stands at 7.0x."),
    )

    client = MockLLMClient(
        response="The company shows material financial weaknesses.",
    )
    generator = LLMReportGenerator(
        client,
        require_indicator_values=True,
    )

    report = generator.generate(analysis)

    assert "20.0%" in report.executive_summary
    assert "€-120,000" in report.executive_summary
    assert "7.0x" in report.executive_summary
    assert "Reported indicator values:" in report.executive_summary


def test_local_llm_report_does_not_duplicate_present_indicator_values() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to 20.0%."),
        make_finding("NFP to EBITDA stands at 7.0x."),
    )

    response = (
        "Revenue growth declined to 20.0% and NFP to EBITDA stands at 7.0x."
    )
    client = MockLLMClient(response=response)
    generator = LLMReportGenerator(
        client,
        require_indicator_values=True,
    )

    report = generator.generate(analysis)

    assert "Reported indicator values:" not in report.executive_summary
    assert report.executive_summary.count("20.0%") == 1
    assert report.executive_summary.count("7.0x") == 1


def test_standard_llm_report_does_not_force_indicator_append() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to 20.0%."),
    )

    client = MockLLMClient(
        response="The company shows material financial weaknesses.",
    )
    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert "20.0%" not in report.executive_summary
    assert "Reported indicator values:" not in report.executive_summary
