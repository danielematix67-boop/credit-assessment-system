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
from src.models.report import ReportFindingGroup
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus


def make_finding(
    text: str = "Test finding.",
    *,
    rule_id: str = "TEST_RULE",
    category: str = "Test Category",
    assessment_area: str | None = None,
    severity: RuleSeverity = RuleSeverity.MEDIUM,
    status: RuleStatus = RuleStatus.TRIGGERED,
) -> AnalysisFinding:
    return AnalysisFinding(
        rule_id=rule_id,
        category=category,
        assessment_area=assessment_area,
        severity=severity,
        text=text,
        status=status,
    )


def make_analysis(
    *,
    status: AssessmentStatus = AssessmentStatus.ATTENTION,
    key_findings: list[AnalysisFinding] | None = None,
    risk_factors: list[AnalysisFinding] | None = None,
    limitations: list[AnalysisFinding] | None = None,
) -> AssessmentAnalysis:
    findings = key_findings if key_findings is not None else []
    return AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=status,
        key_findings=findings,
        risk_factors=risk_factors if risk_factors is not None else findings,
        limitations=limitations if limitations is not None else [],
    )


def make_generator(
    response: str = (
        "Customer profile is unremarkable.\n\n"
        "The company presents relevant financial findings.\n\n"
        "No behavioural anomalies were identified.\n\n"
        "No debt sustainability anomalies were identified."
    ),
    *,
    require_indicator_values: bool = False,
) -> tuple[LLMReportGenerator, MockLLMClient]:
    client = MockLLMClient(response=response)
    return LLMReportGenerator(
        client,
        require_indicator_values=require_indicator_values,
    ), client


def test_implements_report_generator_contract() -> None:
    generator, _ = make_generator()
    assert isinstance(generator, ReportGenerator)


def test_generates_fixed_four_section_llm_narrative_with_deterministic_status() -> None:
    analysis = make_analysis(status=AssessmentStatus.CRITICAL)
    narrative = (
        "No customer anomalies were identified.\n\n"
        "The company presents material financial weaknesses.\n\n"
        "No behavioural anomalies were identified.\n\n"
        "No debt sustainability anomalies were identified."
    )
    generator, _ = make_generator(response=narrative)

    report = generator.generate(analysis)

    assert report.assessment_status == AssessmentStatus.CRITICAL
    assert report.executive_summary == (
        "Assessment Status: Critical\n\n"
        "**Customer Profile**\n\nNo customer anomalies were identified.\n\n"
        "**Financial Analysis**\n\nThe company presents material financial weaknesses.\n\n"
        "**Behavioural Analysis**\n\nNo behavioural anomalies were identified.\n\n"
        "**Debt Sustainability**\n\nNo debt sustainability anomalies were identified."
    )


def test_llm_status_cannot_override_deterministic_status() -> None:
    analysis = make_analysis(status=AssessmentStatus.CRITICAL)
    response = (
        "Assessment status: NORMAL.\n"
        "The company presents material weaknesses.\n\n"
        "No behavioural anomalies were identified.\n\n"
        "No debt sustainability anomalies were identified.\n\n"
        "No customer anomalies were identified."
    )
    generator, _ = make_generator(response=response)

    report = generator.generate(analysis)

    assert report.assessment_status == AssessmentStatus.CRITICAL
    assert "**Customer Profile**" in report.executive_summary
    assert "**Financial Analysis**" in report.executive_summary
    assert "**Behavioural Analysis**" in report.executive_summary
    assert "**Debt Sustainability**" in report.executive_summary
    assert report.executive_summary.count("Assessment Status:") == 1


def test_llm_accepts_section_headings_from_ollama() -> None:
    response = (
        "## Customer Profile\n"
        "The customer profile is stable.\n\n"
        "## Financial Analysis\n"
        "Revenue remains under pressure.\n\n"
        "## Behavioural Analysis\n"
        "No behavioural anomalies were identified.\n\n"
        "## Debt Sustainability\n"
        "Debt sustainability remains adequate."
    )
    generator, _ = make_generator(response=response)

    report = generator.generate(make_analysis())

    assert report.executive_summary == (
        "Assessment Status: Attention\n\n"
        "**Customer Profile**\n\nThe customer profile is stable.\n\n"
        "**Financial Analysis**\n\nRevenue remains under pressure.\n\n"
        "**Behavioural Analysis**\n\nNo behavioural anomalies were identified.\n\n"
        "**Debt Sustainability**\n\nDebt sustainability remains adequate."
    )


def test_llm_rejects_incomplete_or_misordered_section_headings() -> None:
    response = (
        "Customer Profile: Profile.\n\n"
        "Financial Analysis: Financial.\n\n"
        "Debt Sustainability: Debt.\n\n"
        "Behavioural Analysis: Behavioural."
    )
    generator, _ = make_generator(response=response)

    with pytest.raises(ValueError, match="exactly one paragraph for each"):
        generator.generate(make_analysis())


def test_fixed_assessment_area_labels_follow_deterministic_order() -> None:
    findings = [
        make_finding("Customer context.", category="Customer Profile"),
        make_finding("Revenue declined.", category="Financial Analysis"),
        make_finding("Payment delays increased.", category="Behavioural Analysis"),
        make_finding("DSCR remains weak.", category="Debt Sustainability"),
    ]
    narrative = (
        "Customer Profile: Customer context.\n\n"
        "Financial Analysis: Revenue declined.\n\n"
        "Behavioural Analysis: Payment delays increased.\n\n"
        "Debt Sustainability: DSCR remains weak."
    )
    generator, _ = make_generator(response=narrative)

    report = generator.generate(make_analysis(key_findings=findings))

    assert report.executive_summary == (
        "Assessment Status: Attention\n\n"
        "**Customer Profile**\n\nCustomer context.\n\n"
        "**Financial Analysis**\n\nRevenue declined.\n\n"
        "**Behavioural Analysis**\n\nPayment delays increased.\n\n"
        "**Debt Sustainability**\n\nDSCR remains weak."
    )


def test_fixed_assessment_area_labels_use_authoritative_assessment_area() -> None:
    findings = [
        make_finding(
            "Customer context.",
            category="Company Information",
            assessment_area="Customer Profile",
        ),
        make_finding(
            "Revenue declined.",
            category="Revenue",
            assessment_area="Financial Analysis",
        ),
    ]
    narrative = (
        "Customer context.\n\n"
        "Revenue declined.\n\n"
        "No behavioural anomalies were identified.\n\n"
        "No debt sustainability anomalies were identified."
    )
    generator, _ = make_generator(response=narrative)

    report = generator.generate(make_analysis(key_findings=findings))

    assert "**Customer Profile**" in report.executive_summary
    assert "**Financial Analysis**" in report.executive_summary
    assert "###" not in report.executive_summary


def test_fixed_assessment_area_labels_reject_wrong_paragraph_count() -> None:
    findings = [
        make_finding("Customer context.", category="Customer Profile"),
        make_finding("Revenue declined.", category="Financial Analysis"),
    ]
    generator, _ = make_generator(
        response="Paragraph one.\n\nParagraph two.\n\nParagraph three."
    )

    with pytest.raises(ValueError, match="exactly one paragraph for each"):
        generator.generate(make_analysis(key_findings=findings))


def test_rejects_empty_response() -> None:
    generator, _ = make_generator(response="")

    with pytest.raises(ValueError, match="LLM returned an empty response"):
        generator.generate(make_analysis())


def test_extracts_indicator_values_from_findings() -> None:
    findings = [
        make_finding("Revenue growth declined to -20.0%."),
        make_finding("EBITDA is negative at €-120,000."),
        make_finding("NFP to EBITDA stands at 7.0x."),
        make_finding("Revenue growth also equals -20.0%."),
    ]

    assert LLMReportGenerator._extract_indicator_values(findings) == [
        "-20.0%",
        "€-120,000",
        "7.0x",
    ]


def test_indicator_grounding_allows_omitted_source_indicators() -> None:
    findings = [
        make_finding("Revenue growth declined to -20.0%.", category="Revenue"),
        make_finding(
            "EBITDA is negative at €-120,000.",
            category="Profitability",
        ),
        make_finding(
            "NFP to EBITDA stands at 7.0x.\n\n"
            "No behavioural anomalies were identified.\n\n"
            "No debt sustainability anomalies were identified.",
            category="Leverage",
        ),
    ]
    analysis = make_analysis(
        status=AssessmentStatus.CRITICAL,
        key_findings=findings,
    )
    response = (
        "Customer profile is unremarkable.\n\n"
        "EBITDA is negative and leverage remains elevated.\n\n"
        "No behavioural anomalies were identified.\n\n"
        "No debt sustainability anomalies were identified."
    )
    generator, _ = make_generator(
        response=response,
        require_indicator_values=True,
    )

    report = generator.generate(analysis)

    assert "**Financial Analysis**" in report.executive_summary


def test_indicator_grounding_accepts_equivalent_numeric_formatting() -> None:
    findings = [
        make_finding("Revenue growth declined to -20.0%.", category="Revenue"),
        make_finding("NFP to EBITDA stands at 7.0x.", category="Leverage"),
    ]
    response = (
        "Customer profile is unremarkable.\n\n"
        "Revenue growth declined to -20% and NFP to EBITDA stands at 7x.\n\n"
        "No behavioural anomalies were identified.\n\n"
        "No debt sustainability anomalies were identified."
    )
    generator, _ = make_generator(
        response=response,
        require_indicator_values=True,
    )

    report = generator.generate(make_analysis(key_findings=findings))

    assert (
        "Revenue growth declined to -20% and NFP to EBITDA stands at 7x."
        in report.executive_summary
    )


def test_indicator_grounding_accepts_decimal_comma_formatting() -> None:
    findings = [
        make_finding("Revenue growth declined to -20.0%.", category="Revenue"),
    ]
    response = (
        "Customer profile is unremarkable.\n\n"
        "Revenue growth declined to -20,0%.\n\n"
        "No behavioural anomalies were identified.\n\n"
        "No debt sustainability anomalies were identified."
    )
    generator, _ = make_generator(
        response=response,
        require_indicator_values=True,
    )

    report = generator.generate(make_analysis(key_findings=findings))

    assert "Revenue growth declined to -20,0%." in report.executive_summary

def test_indicator_grounding_sanitizes_unsupported_numeric_values() -> None:
    findings = [
        make_finding("Revenue growth declined to -20.0%.", category="Revenue"),
    ]
    generator, _ = make_generator(
        response=(
            "Customer profile is unremarkable.\n\n"
            "Revenue growth declined to -35%. "
            "The overall financial profile remains under pressure.\n\n"
            "No behavioural anomalies were identified.\n\n"
            "No debt sustainability anomalies were identified."
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
        "Customer profile is unremarkable.\n\n"
        "Revenue growth declined to 20.0% and NFP to EBITDA stands at 7.0x.\n\n"
        "No behavioural anomalies were identified.\n\n"
        "No debt sustainability anomalies were identified."
    )
    generator, _ = make_generator(
        response=response,
        require_indicator_values=True,
    )

    report = generator.generate(make_analysis(key_findings=findings))

    assert (
        "Revenue growth declined to 20.0% and NFP to EBITDA stands at 7.0x."
        in report.executive_summary
    )



def test_standard_llm_does_not_force_indicator_grounding() -> None:
    analysis = make_analysis(
        key_findings=[make_finding("Revenue growth declined to 20.0%.")]
    )
    generator, _ = make_generator(require_indicator_values=False)

    report = generator.generate(analysis)

    assert "20.0%" not in report.executive_summary


def test_preserves_structured_data() -> None:
    findings = [
        make_finding("Revenue finding.", category="Revenue"),
        make_finding("Profitability finding.", category="Profitability"),
    ]
    limitations = [make_finding("Missing data.", category="Limitations")]
    analysis = make_analysis(
        key_findings=findings,
        limitations=limitations,
    )
    generator, _ = make_generator()

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.limitations == limitations
    assert report.findings_by_category == [
        ReportFindingGroup(category="Revenue", findings=[findings[0]]),
        ReportFindingGroup(category="Profitability", findings=[findings[1]]),
    ]


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
