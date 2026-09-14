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


def make_finding(text: str, category: str = "Financial Risk") -> AnalysisFinding:
    return AnalysisFinding(
        rule_id="R001",
        category=category,
        severity=RuleSeverity.HIGH,
        text=text,
        status=RuleStatus.TRIGGERED,
    )


def test_prompt_allows_narrative_synthesis_without_forcing_every_value() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to 20.0%.", category="revenue"),
        make_finding("EBITDA is negative at €-120,000.", category="profitability"),
    )

    prompt = ReportPromptBuilder().build(analysis)

    assert "Equivalent numeric formatting is allowed" in prompt
    assert "Report only what is contained in the supplied Analysis findings" in prompt
    assert "Do not invent facts, causes, consequences or recommendations" in prompt
    assert "1. revenue" in prompt
    assert "2. profitability" in prompt


def test_local_llm_accepts_narrative_when_some_source_indicators_are_omitted() -> None:
    findings = [
        make_finding("Revenue growth declined to -20.0%.", category="revenue"),
        make_finding("EBITDA is negative at €-120,000.", category="profitability"),
        make_finding("NFP to EBITDA stands at 7.0x.", category="leverage"),
    ]
    analysis = make_analysis(*findings)
    response = (
        "The company shows material financial weaknesses. "
        "EBITDA is negative and leverage remains elevated."
    )
    generator = LLMReportGenerator(
        MockLLMClient(response=response),
        require_indicator_values=True,
    )

    report = generator.generate(analysis)

    assert report.executive_summary.endswith(response)
    assert "Revenue growth declined to -20.0%." not in report.executive_summary


def test_local_llm_accepts_equivalent_indicator_formatting() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to -20.0%.", category="revenue"),
        make_finding("NFP to EBITDA stands at 7.0x.", category="leverage"),
    )
    response = "Revenue growth declined to -20% and NFP to EBITDA stands at 7x."
    generator = LLMReportGenerator(
        MockLLMClient(response=response),
        require_indicator_values=True,
    )

    report = generator.generate(analysis)

    assert report.executive_summary.endswith(response)


def test_local_llm_rejects_unsupported_indicator_values() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to -20.0%.", category="revenue"),
    )
    generator = LLMReportGenerator(
        MockLLMClient(response="Revenue growth declined to -35%."),
        require_indicator_values=True,
    )

    try:
        generator.generate(analysis)
    except ValueError as exc:
        assert "unsupported indicator value" in str(exc)
    else:
        raise AssertionError("Unsupported indicator value was accepted")


def test_local_llm_does_not_duplicate_present_indicator_values() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to 20.0%.", category="revenue"),
        make_finding("NFP to EBITDA stands at 7.0x.", category="leverage"),
    )
    response = (
        "Revenue growth declined to 20.0% and NFP to EBITDA stands at 7.0x."
    )
    generator = LLMReportGenerator(
        MockLLMClient(response=response),
        require_indicator_values=True,
    )

    report = generator.generate(analysis)

    assert report.executive_summary.count("20.0%") == 1
    assert report.executive_summary.count("7.0x") == 1


def test_llm_status_is_deterministic_and_on_one_line() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to -20.0%."),
    )
    client = MockLLMClient(
        response=(
            "Assessment status: CRITICAL.\n"
            "Revenue growth declined to -20.0%."
        ),
    )
    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)
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
