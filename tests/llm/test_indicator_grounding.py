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


def make_finding(text: str, category: str = "Financial Risk") -> AnalysisFinding:
    return AnalysisFinding(
        rule_id="R001",
        category=category,
        severity=RuleSeverity.HIGH,
        text=text,
    )


def test_prompt_requires_values_order_and_no_repetition() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to 20.0%.", category="revenue"),
        make_finding("EBITDA is negative at €-120,000.", category="profitability"),
    )

    prompt = ReportPromptBuilder().build(analysis)

    assert "Every material numerical indicator" in prompt
    assert "must appear in the narrative" in prompt
    assert "Do not round, recalculate, convert or replace" in prompt
    assert "1. revenue" in prompt
    assert "2. profitability" in prompt
    assert "one narrative paragraph for each category" in prompt
    assert "Never return to a category after moving to the next category" in prompt
    assert "Mention each material indicator value once" in prompt


def test_local_llm_adds_only_missing_indicator_value_concisely() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to -20.0%.", category="revenue"),
        make_finding("EBITDA is negative at €-120,000.", category="profitability"),
        make_finding("NFP to EBITDA stands at 7.0x.", category="leverage"),
    )

    client = MockLLMClient(
        response=(
            "The company shows material financial weaknesses. "
            "EBITDA is negative at €-120,000 and leverage stands at 7.0x."
        ),
    )
    generator = LLMReportGenerator(client, require_indicator_values=True)

    report = generator.generate(analysis)
    summary = report.executive_summary

    assert summary.count("-20.0%") == 1
    assert summary.count("€-120,000") == 1
    assert summary.count("7.0x") == 1
    assert "Revenue growth: -20.0%." in summary
    assert "The assessment also reflects:" not in summary
    assert "Revenue growth declined to -20.0%." not in summary
    assert "Reported indicator values:" not in summary


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
    assert "Reported indicator values:" not in report.executive_summary
    assert "The assessment also reflects:" not in report.executive_summary


def test_llm_status_is_deterministic_descriptive_and_on_one_line() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to -20.0%."),
    )

    client = MockLLMClient(
        response=(
            "Assessment status: CRITICAL.\n"
            "The company shows material financial weaknesses."
        ),
    )
    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)
    lines = report.executive_summary.splitlines()

    assert lines[0] == (
        "Assessment status: CRITICAL — "
        "Significant credit-risk factors affecting the credit profile identified."
    )
    assert lines[1] == "The company shows material financial weaknesses."
    assert report.executive_summary.count("Assessment status:") == 1


def test_duplicate_sentences_are_removed_from_llm_output() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to -20.0%."),
    )
    response = (
        "Revenue growth is deteriorating. Revenue growth is deteriorating. "
        "EBITDA is negative."
    )

    generator = LLMReportGenerator(MockLLMClient(response=response))
    report = generator.generate(analysis)

    assert report.executive_summary.count("Revenue growth is deteriorating.") == 1
    assert report.executive_summary.count("EBITDA is negative.") == 1


def test_standard_llm_report_does_not_force_indicator_append() -> None:
    analysis = make_analysis(
        make_finding("Revenue growth declined to 20.0%."),
    )
    generator = LLMReportGenerator(
        MockLLMClient(response="The company shows material financial weaknesses.")
    )

    report = generator.generate(analysis)

    assert "20.0%" not in report.executive_summary
    assert "Reported indicator values:" not in report.executive_summary


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
