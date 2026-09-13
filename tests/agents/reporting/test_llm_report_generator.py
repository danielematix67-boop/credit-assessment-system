from unittest.mock import MagicMock

import pytest

from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.llm.mock_client import MockLLMClient
from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report, ReportFindingGroup
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus


def make_finding(text: str = "Test finding.", *, rule_id: str = "TEST_RULE", category: str = "Test Category", severity: RuleSeverity = RuleSeverity.MEDIUM, status: RuleStatus = RuleStatus.TRIGGERED) -> AnalysisFinding:
    return AnalysisFinding(rule_id=rule_id, category=category, severity=severity, text=text, status=status)


def make_analysis(*, status: AssessmentStatus = AssessmentStatus.ATTENTION, key_findings: list[AnalysisFinding] | None = None, risk_factors: list[AnalysisFinding] | None = None, limitations: list[AnalysisFinding] | None = None) -> AssessmentAnalysis:
    findings = key_findings if key_findings is not None else []
    return AssessmentAnalysis(position_id="TEST_POSITION", assessment_status=status, key_findings=findings, risk_factors=risk_factors if risk_factors is not None else findings, limitations=limitations if limitations is not None else [])


def make_generator(response: str = "The company presents relevant financial findings.", *, require_indicator_values: bool = False) -> tuple[LLMReportGenerator, MockLLMClient]:
    client = MockLLMClient(response=response)
    return LLMReportGenerator(client, require_indicator_values=require_indicator_values), client


def expected_status_line(status: AssessmentStatus) -> str:
    return f"Assessment Status: {status.value.capitalize()}"


def test_implements_report_generator_contract() -> None:
    generator, _ = make_generator()
    assert isinstance(generator, ReportGenerator)


def test_accepts_llm_client_contract() -> None:
    client = MagicMock(spec=LLMClient)
    client.generate.return_value = "Generated narrative."
    generator = LLMReportGenerator(client)
    report = generator.generate(make_analysis())
    assert isinstance(report, Report)
    client.generate.assert_called_once()


def test_accepts_custom_prompt_builder() -> None:
    client = MagicMock(spec=LLMClient)
    client.generate.return_value = "Generated narrative."
    prompt_builder = MagicMock(spec=ReportPromptBuilder)
    prompt_builder.build.return_value = "Test prompt"
    generator = LLMReportGenerator(client, prompt_builder=prompt_builder)
    generator.generate(make_analysis())
    assert generator.prompt_builder is prompt_builder
    prompt_builder.build.assert_called_once()
    client.generate.assert_called_once_with("Test prompt")


def test_generates_report_with_deterministic_status_and_narrative() -> None:
    analysis = make_analysis(status=AssessmentStatus.ATTENTION)
    narrative = "Revenue and profitability show material weaknesses."
    generator, _ = make_generator(response=narrative)
    report = generator.generate(analysis)
    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.executive_summary == f"{expected_status_line(analysis.assessment_status)}\n\n{narrative}"


@pytest.mark.parametrize("status", list(AssessmentStatus))
def test_status_line_is_title_case_and_separate_from_narrative(status: AssessmentStatus) -> None:
    analysis = make_analysis(status=status)
    generator, _ = make_generator(response="Generated narrative.")
    report = generator.generate(analysis)
    lines = report.executive_summary.splitlines()
    assert lines[0] == expected_status_line(status)
    assert lines[1] == ""
    assert lines[2] == "Generated narrative."
    assert report.executive_summary.count("Assessment Status:") == 1


def test_llm_generated_status_is_removed_and_cannot_override_deterministic_status() -> None:
    analysis = make_analysis(status=AssessmentStatus.CRITICAL)
    response = "Assessment status: NORMAL.\nThe company presents material financial weaknesses."
    generator, _ = make_generator(response=response)
    report = generator.generate(analysis)
    assert report.assessment_status == AssessmentStatus.CRITICAL
    assert report.executive_summary == "Assessment Status: Critical\n\nThe company presents material financial weaknesses."
    assert report.executive_summary.count("Assessment Status:") == 1


@pytest.mark.parametrize("response", ["Assessment status: CRITICAL.\nNarrative.", "Assessment status: ATTENTION — some description.\nNarrative.", "assessment status: NORMAL.\nNarrative."])
def test_removes_llm_status_prefix_case_insensitively(response: str) -> None:
    generator, _ = make_generator(response=response)
    report = generator.generate(make_analysis())
    assert report.executive_summary.endswith("Narrative.")
    assert report.executive_summary.count("Assessment Status:") == 1


def test_rejects_empty_response() -> None:
    generator, _ = make_generator(response="")
    with pytest.raises(ValueError, match="LLM returned an empty response"):
        generator.generate(make_analysis())


@pytest.mark.parametrize("response", [" ", "\n", "\t", "  \n\t  "])
def test_rejects_whitespace_response(response: str) -> None:
    generator, _ = make_generator(response=response)
    with pytest.raises(ValueError, match="LLM returned an empty response"):
        generator.generate(make_analysis())


def test_rejects_status_only_response_after_status_prefix_is_removed() -> None:
    generator, _ = make_generator(response="Assessment status: CRITICAL.")
    with pytest.raises(ValueError, match="LLM returned an empty narrative"):
        generator.generate(make_analysis())


def test_strips_response_whitespace() -> None:
    generator, _ = make_generator(response="  Generated narrative.  ")
    report = generator.generate(make_analysis())
    assert report.executive_summary == "Assessment Status: Attention\n\nGenerated narrative."


def test_preserves_repeated_sentences_without_aggressive_rewriting() -> None:
    response = "Revenue growth declined. EBITDA is negative. Revenue growth declined. EBITDA is negative."
    generator, _ = make_generator(response=response)
    report = generator.generate(make_analysis())
    assert report.executive_summary.endswith(response)


def test_extracts_indicator_values_from_findings() -> None:
    findings = [make_finding("Revenue growth declined to -20.0%."), make_finding("EBITDA is negative at €-120,000."), make_finding("NFP to EBITDA stands at 7.0x."), make_finding("Revenue growth also equals -20.0%.")]
    assert LLMReportGenerator._extract_indicator_values(findings) == ["-20.0%", "€-120,000", "7.0x"]


def test_indicator_grounding_allows_omitted_source_indicators() -> None:
    findings = [make_finding("Revenue growth declined to -20.0%.", category="Revenue"), make_finding("EBITDA is negative at €-120,000.", category="Profitability"), make_finding("NFP to EBITDA stands at 7.0x.", category="Leverage")]
    analysis = make_analysis(status=AssessmentStatus.CRITICAL, key_findings=findings)
    response = "EBITDA is negative and leverage remains elevated."
    generator, _ = make_generator(response=response, require_indicator_values=True)
    report = generator.generate(analysis)
    assert report.executive_summary == "Assessment Status: Critical\n\n" + response


def test_indicator_grounding_accepts_equivalent_numeric_formatting() -> None:
    findings = [make_finding("Revenue growth declined to -20.0%.", category="Revenue"), make_finding("NFP to EBITDA stands at 7.0x.", category="Leverage")]
    analysis = make_analysis(key_findings=findings)
    response = "Revenue growth declined to -20% and NFP to EBITDA stands at 7x."
    generator, _ = make_generator(response=response, require_indicator_values=True)
    report = generator.generate(analysis)
    assert report.executive_summary.endswith(response)


def test_indicator_grounding_accepts_decimal_comma_formatting() -> None:
    findings = [make_finding("Revenue growth declined to -20.0%.", category="Revenue")]
    analysis = make_analysis(key_findings=findings)
    response = "Revenue growth declined to -20,0%."
    generator, _ = make_generator(response=response, require_indicator_values=True)
    report = generator.generate(analysis)
    assert report.executive_summary.endswith(response)


def test_indicator_grounding_rejects_unsupported_numeric_values() -> None:
    findings = [make_finding("Revenue growth declined to -20.0%.", category="Revenue")]
    analysis = make_analysis(key_findings=findings)
    generator, _ = make_generator(response="Revenue growth declined to -35%.", require_indicator_values=True)
    with pytest.raises(ValueError, match="unsupported indicator value"):
        generator.generate(analysis)


def test_local_llm_does_not_fallback_when_all_indicator_values_are_present() -> None:
    findings = [make_finding("Revenue growth declined to 20.0%.", category="Revenue"), make_finding("NFP to EBITDA stands at 7.0x.", category="Leverage")]
    analysis = make_analysis(key_findings=findings)
    response = "Revenue growth declined to 20.0% and NFP to EBITDA stands at 7.0x."
    generator, _ = make_generator(response=response, require_indicator_values=True)
    report = generator.generate(analysis)
    assert report.executive_summary.endswith(response)
    assert report.executive_summary.count("20.0%") == 1
    assert report.executive_summary.count("7.0x") == 1


def test_standard_llm_does_not_force_indicator_grounding() -> None:
    analysis = make_analysis(key_findings=[make_finding("Revenue growth declined to 20.0%.")])
    generator, _ = make_generator(require_indicator_values=False)
    report = generator.generate(analysis)
    assert "20.0%" not in report.executive_summary


def test_prompt_contains_authoritative_category_order() -> None:
    findings = [make_finding("Leverage finding.", category="leverage"), make_finding("Revenue finding.", category="revenue"), make_finding("Profitability finding.", category="profitability")]
    prompt = ReportPromptBuilder().build(make_analysis(key_findings=findings))
    assert prompt.index("1. revenue") < prompt.index("2. profitability") < prompt.index("3. leverage")
    assert "Discuss each category at most once." in prompt
    assert "Never return to a category after moving to the next category." in prompt
    assert "Do not repeat an indicator" in prompt
    assert "Mention each material indicator value once" in prompt
    assert "Do not generate the assessment status." in prompt
    assert "Do not infer sales volume, pricing" in prompt


def test_preserves_structured_data() -> None:
    findings = [make_finding("Revenue finding.", category="Revenue"), make_finding("Profitability finding.", category="Profitability")]
    limitations = [make_finding("Missing data.", category="Limitations")]
    analysis = make_analysis(key_findings=findings, limitations=limitations)
    generator, _ = make_generator()
    report = generator.generate(analysis)
    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.limitations == limitations
    assert report.findings_by_category == [ReportFindingGroup(category="Revenue", findings=[findings[0]]), ReportFindingGroup(category="Profitability", findings=[findings[1]])]


def test_group_findings_by_category_preserves_order() -> None:
    findings = [make_finding("Finding 1.", category="Revenue"), make_finding("Finding 2.", category="Profitability"), make_finding("Finding 3.", category="Revenue")]
    assert LLMReportGenerator._group_findings_by_category(findings) == [ReportFindingGroup(category="Revenue", findings=[findings[0], findings[2]]), ReportFindingGroup(category="Profitability", findings=[findings[1]])]


def test_does_not_modify_analysis() -> None:
    findings = [make_finding("Revenue growth declined to -20.0%.")]
    analysis = make_analysis(key_findings=findings)
    original = (list(analysis.key_findings), list(analysis.risk_factors), list(analysis.limitations))
    generator, _ = make_generator(require_indicator_values=True)
    generator.generate(analysis)
    assert analysis.key_findings == original[0]
    assert analysis.risk_factors == original[1]
    assert analysis.limitations == original[2]


def test_propagates_client_errors() -> None:
    client = MagicMock(spec=LLMClient)
    client.generate.side_effect = RuntimeError("LLM service unavailable")
    prompt_builder = MagicMock(spec=ReportPromptBuilder)
    prompt_builder.build.return_value = "Test prompt"
    generator = LLMReportGenerator(client, prompt_builder=prompt_builder)
    with pytest.raises(RuntimeError, match="LLM service unavailable"):
        generator.generate(make_analysis())
    prompt_builder.build.assert_called_once()
    client.generate.assert_called_once_with("Test prompt")


def test_discursive_narrative_preserves_all_findings_and_indicators() -> None:
    findings = [make_finding("Revenue growth declined to -20.0%, indicating a deterioration in the company's top-line performance.", category="Revenue"), make_finding("EBITDA is negative, with a reported value of €-120,000, indicating negative operating profitability.", category="Profitability"), make_finding("The interest coverage ratio is -0.2x, indicating that EBITDA provides insufficient coverage of interest expense.", category="Profitability"), make_finding("EBITDA margin is -8.0%.", category="Profitability"), make_finding("NFP to EBITDA stands at 7.0x, above the acceptable level, indicating elevated leverage relative to operating earnings.", category="Leverage")]
    analysis = make_analysis(status=AssessmentStatus.CRITICAL, key_findings=findings)
    response = ("Revenue growth declined to -20.0%, indicating a deterioration in the company's top-line performance.\n\n" "EBITDA is negative, with a reported value of €-120,000, indicating negative operating profitability. The interest coverage ratio is -0.2x, indicating that EBITDA provides insufficient coverage of interest expense. EBITDA margin is -8.0%.\n\n" "NFP to EBITDA stands at 7.0x, above the acceptable level, indicating elevated leverage relative to operating earnings.")
    generator, _ = make_generator(response=response, require_indicator_values=True)
    report = generator.generate(analysis)
    assert report.executive_summary == "Assessment Status: Critical\n\n" + response
    for finding in findings:
        assert finding.text.split(",")[0] in report.executive_summary
    for value in LLMReportGenerator._extract_indicator_values(findings):
        assert report.executive_summary.count(value) == 1
