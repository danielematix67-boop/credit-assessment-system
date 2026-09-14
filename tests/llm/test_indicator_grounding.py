from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.llm.mock_client import MockLLMClient
from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus


def make_analysis(*findings: AnalysisFinding) -> AssessmentAnalysis:
    return AssessmentAnalysis(
        position_id="TEST-INDICATORS",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=list(findings),
        risk_factors=list(findings),
        limitations=[],
    )


def make_finding(
    text: str,
    category: str = "Financial Risk",
    *,
    value: object | None = None,
    indicator: str = "",
) -> AnalysisFinding:
    return AnalysisFinding(
        rule_id="R001",
        category=category,
        severity=RuleSeverity.HIGH,
        text=text,
        status=RuleStatus.TRIGGERED,
        value=value,
        indicator=indicator,
    )


def test_prompt_requires_qualitative_narrative_and_deterministic_numeric_rendering() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to 20.0%.", category="revenue"),
        make_finding("EBITDA is negative at €-120,000.", category="profitability"),
    )
    prompt = ReportPromptBuilder().build(analysis)
    assert "Do not reproduce percentages, monetary amounts, ratios" in prompt
    assert (
        "The application, not the LLM, is responsible for rendering "
        "authoritative numeric indicator values"
    ) in prompt
    assert "1. revenue" in prompt
    assert "2. profitability" in prompt


def test_prompt_preserves_structured_indicator_value_as_source_evidence() -> None:
    analysis = make_analysis(
        make_finding(
            "Revenue growth declined to -35.0%.",
            category="Financial Analysis",
            value=-0.35,
            indicator="Revenue growth",
        ),
    )
    prompt = ReportPromptBuilder().build(analysis)
    assert "Deterministic indicator: Revenue growth" in prompt
    assert "Deterministic value: -35.0%" in prompt
    assert "Revenue growth declined to -35.0%." in prompt
    assert "rule_id" not in prompt


def test_llm_accepts_qualitative_narrative_without_numeric_values() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to -20.0%.", category="revenue"),
        make_finding(
            "EBITDA is negative at €-120,000.",
            category="profitability",
        ),
    )
    response = (
        "The company shows material financial weaknesses. "
        "EBITDA remains negative and profitability is under pressure."
    )
    report = LLMReportGenerator(
        MockLLMClient(response=response),
        require_indicator_values=True,
    ).generate(analysis)
    assert report.executive_summary.endswith(response)


def test_llm_accepts_equivalent_source_indicator_formatting() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to -20.0%.", category="revenue"),
        make_finding("NFP to EBITDA stands at 7.0x.", category="leverage"),
    )
    response = "Revenue growth declined to -20% and NFP to EBITDA stands at 7x."
    report = LLMReportGenerator(
        MockLLMClient(response=response),
        require_indicator_values=True,
    ).generate(analysis)
    assert report.executive_summary.endswith(response)


def test_llm_sanitizes_unsupported_indicator_values_instead_of_falling_back() -> None:
    analysis = make_analysis(
        make_finding(
            "Revenue growth declined to -35.0%.",
            value=-0.35,
            indicator="Revenue growth",
        ),
    )
    response = (
        "Revenue growth declined to 35.0%. "
        "The overall financial profile remains under pressure."
    )
    report = LLMReportGenerator(
        MockLLMClient(response=response),
        require_indicator_values=True,
    ).generate(analysis)
    assert "35.0%" not in report.executive_summary
    assert "overall financial profile remains under pressure" in report.executive_summary
    assert "Revenue growth declined to -35.0%." in " ".join(
        finding.text
        for group in report.findings_by_category
        for finding in group.findings
    )


def test_llm_does_not_duplicate_present_indicator_values() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to 20.0%.", category="revenue"),
        make_finding("NFP to EBITDA stands at 7.0x.", category="leverage"),
    )
    response = "Revenue growth declined to 20.0% and NFP to EBITDA stands at 7.0x."
    report = LLMReportGenerator(
        MockLLMClient(response=response),
        require_indicator_values=True,
    ).generate(analysis)
    assert report.executive_summary.count("20.0%") == 1
    assert report.executive_summary.count("7.0x") == 1


def test_llm_status_is_deterministic_and_on_one_line() -> None:
    analysis = make_analysis(make_finding("Revenue growth declined to -20.0%."))
    client = MockLLMClient(
        response=(
            "Assessment status: CRITICAL.\n"
            "Revenue growth declined to -20.0%."
        ),
    )
    report = LLMReportGenerator(client).generate(analysis)
    lines = report.executive_summary.splitlines()
    assert lines[0] == "Assessment Status: Critical"
    assert lines[1] == ""
    assert lines[2] == "Revenue growth declined to -20.0%."
    assert report.executive_summary.count("Assessment Status:") == 1


def test_ollama_workflow_enables_indicator_grounding() -> None:
    from app.workflow.assessment_workflow_factory import create_workflow

    workflow = create_workflow(
        "Ollama + Fallback",
        ollama_host="http://localhost:11434",
        ollama_model="qwen3:0.6b",
    )
    generator = workflow.reporting_agent.report_generator
    assert isinstance(generator, LLMReportGenerator)
    assert generator.require_indicator_values is True
