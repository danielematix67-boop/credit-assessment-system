from unittest.mock import MagicMock

import pytest

from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.llm.mock_client import MockLLMClient
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report, ReportFindingGroup
from src.rules.base.severity import RuleSeverity


# ============================================================
# Fixtures / Factories
# ============================================================


def make_analysis_finding(
    *,
    rule_id: str = "TEST_RULE",
    category: str = "Test Category",
    severity: RuleSeverity = RuleSeverity.MEDIUM,
    text: str = "Test finding.",
) -> AnalysisFinding:
    return AnalysisFinding(
        rule_id=rule_id,
        category=category,
        severity=severity,
        text=text,
    )


def make_analysis(
    *,
    position_id: str = "TEST_POSITION",
    status: AssessmentStatus = AssessmentStatus.ATTENTION,
    key_findings: list[AnalysisFinding] | None = None,
    risk_factors: list[AnalysisFinding] | None = None,
    limitations: list[AnalysisFinding] | None = None,
) -> AssessmentAnalysis:
    return AssessmentAnalysis(
        position_id=position_id,
        assessment_status=status,
        key_findings=(
            key_findings
            if key_findings is not None
            else []
        ),
        risk_factors=(
            risk_factors
            if risk_factors is not None
            else []
        ),
        limitations=(
            limitations
            if limitations is not None
            else []
        ),
    )


@pytest.fixture
def analysis() -> AssessmentAnalysis:
    findings = [
        make_analysis_finding(
            rule_id=f"RULE_{index}",
            category=category,
            severity=severity,
            text=f"Finding {index}.",
        )
        for index, (category, severity) in enumerate(
            [
                ("Revenue", RuleSeverity.MEDIUM),
                ("Profitability", RuleSeverity.HIGH),
                ("Profitability", RuleSeverity.MEDIUM),
                ("Leverage", RuleSeverity.HIGH),
            ],
            start=1,
        )
    ]

    risk_factors = [
        finding
        for finding in findings
        if finding.severity == RuleSeverity.HIGH
    ]

    limitations = [
        make_analysis_finding(
            rule_id=f"LIMITATION_{index}",
            category="Limitation Category",
            severity=RuleSeverity.MEDIUM,
            text=f"Limitation {index}.",
        )
        for index in range(1, 3)
    ]

    return make_analysis(
        position_id="TEST_POSITION",
        status=AssessmentStatus.ATTENTION,
        key_findings=findings,
        risk_factors=risk_factors,
        limitations=limitations,
    )


def valid_response(
    analysis: AssessmentAnalysis,
) -> str:
    return (
        "The assessment identified relevant findings."
    )


def different_status(
    status: AssessmentStatus,
) -> AssessmentStatus:
    return next(
        candidate
        for candidate in AssessmentStatus
        if candidate != status
    )


# ============================================================
# Helpers
# ============================================================


def generate_report(
    analysis: AssessmentAnalysis,
    response: str | None = None,
) -> tuple[LLMReportGenerator, Report, MockLLMClient]:
    client = MockLLMClient(
        response=(
            response
            if response is not None
            else valid_response(analysis)
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    return generator, report, client


def report_findings(
    report: Report,
) -> list[AnalysisFinding]:
    return [
        finding
        for group in report.findings_by_category
        for finding in group.findings
    ]


def findings_by_category_from_analysis(
    analysis: AssessmentAnalysis,
) -> list[ReportFindingGroup]:
    categories: dict[
        str,
        list[AnalysisFinding],
    ] = {}

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


def prompt_contains_all(
    prompt: str,
    values: list[str],
) -> bool:
    return all(
        value in prompt
        for value in values
    )


# ============================================================
# Contract
# ============================================================


def test_llm_report_generator_implements_report_generator_contract(
    analysis,
):
    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    assert isinstance(
        generator,
        ReportGenerator,
    )


def test_llm_report_generator_accepts_llm_client_contract(
    analysis,
):
    client = MagicMock(
        spec=LLMClient,
    )

    client.generate.return_value = valid_response(
        analysis,
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert isinstance(
        report,
        Report,
    )


# ============================================================
# Basic generation
# ============================================================


def test_llm_report_generator_generates_report(
    analysis,
):
    _, report, client = generate_report(
        analysis,
    )

    assert isinstance(
        report,
        Report,
    )

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status

    expected_summary = (
        f"Assessment status: "
        f"{analysis.assessment_status.value}.\n"
        f"{client.response}"
    )

    assert report.executive_summary == expected_summary


def test_llm_report_generator_invokes_llm_client(
    analysis,
):
    client = MagicMock(
        spec=LLMClient,
    )

    client.generate.return_value = valid_response(
        analysis,
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

    client.generate.assert_called_once()


# ============================================================
# Deterministic status ownership
# ============================================================


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_llm_report_generator_uses_deterministic_status(
    status,
):
    analysis = make_analysis(
        status=status,
    )

    llm_response = (
        "The company presents several financial findings."
    )

    _, report, _ = generate_report(
        analysis,
        response=llm_response,
    )

    assert report.assessment_status == status

    assert report.executive_summary.startswith(
        f"Assessment status: {status.value}."
    )


def test_llm_report_generator_llm_does_not_control_report_status(
    analysis,
):
    different = different_status(
        analysis.assessment_status,
    )

    llm_response = (
        f"The company is classified as {different.value} "
        "based on the observed financial indicators."
    )

    _, report, _ = generate_report(
        analysis,
        response=llm_response,
    )

    assert report.assessment_status == (
        analysis.assessment_status
    )


def test_llm_report_generator_adds_status_to_llm_narrative(
    analysis,
):
    narrative = (
        "Revenue and profitability indicators show "
        "material weaknesses."
    )

    _, report, _ = generate_report(
        analysis,
        response=narrative,
    )

    assert report.executive_summary == (
        f"Assessment status: "
        f"{analysis.assessment_status.value}.\n"
        f"{narrative}"
    )


# ============================================================
# Prompt construction
# ============================================================


def test_llm_report_generator_includes_assessment_status(
    analysis,
):
    _, _, client = generate_report(
        analysis,
    )

    assert (
        analysis.assessment_status.value
        in client.last_prompt
    )


def test_llm_report_generator_includes_all_analysis_content(
    analysis,
):
    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt

    findings = (
        analysis.key_findings
        + analysis.risk_factors
        + analysis.limitations
    )

    for finding in findings:
        assert finding.category in prompt
        assert finding.text in prompt


def test_llm_report_generator_includes_finding_metadata(
    analysis,
):
    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt

    findings = (
        analysis.key_findings
        + analysis.risk_factors
        + analysis.limitations
    )

    for finding in findings:
        assert finding.rule_id in prompt
        assert finding.category in prompt
        assert finding.severity.value in prompt
        assert finding.text in prompt


def test_llm_report_generator_includes_structured_sections(
    analysis,
):
    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt.lower()

    expected_sections = [
        "assessment status",
        "key findings",
        "risk factors",
        "limitations",
    ]

    assert prompt_contains_all(
        prompt,
        expected_sections,
    )


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_llm_report_generator_includes_configured_status_in_prompt(
    status,
):
    analysis = make_analysis(
        status=status,
    )

    _, _, client = generate_report(
        analysis,
    )

    assert (
        analysis.assessment_status.value
        in client.last_prompt
    )


# ============================================================
# Prompt semantic contract
# ============================================================


def test_llm_report_generator_prompt_separates_deterministic_assessment_from_generation(
    analysis,
):
    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt.lower()

    assert "deterministic" in prompt
    assert "assessment" in prompt
    assert "your role" in prompt

    generation_terms = [
        "generate",
        "summary",
        "language",
        "summaris",
    ]

    assert any(
        term in prompt
        for term in generation_terms
    )


def test_llm_report_generator_prompt_contains_core_safety_constraints(
    analysis,
):
    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt.lower()

    safety_concepts = [
        "source of truth",
        "do not reassess",
        "do not modify",
        "do not invent",
        "credit decision",
        "do not override",
        "threshold",
    ]

    for keyword in safety_concepts:
        assert keyword in prompt


def test_llm_report_generator_prompt_protects_deterministic_assessment(
    analysis,
):
    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt.lower()

    required_concepts = [
        "deterministic",
        "source of truth",
        "assessment status",
        "severity",
        "do not modify",
        "do not override",
        "credit decision",
    ]

    assert prompt_contains_all(
        prompt,
        required_concepts,
    )


def test_llm_report_generator_prompt_requires_factual_grounding(
    analysis,
):
    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt.lower()

    grounding_concepts = [
        "information provided",
        "do not invent",
        "do not introduce",
        "assessment",
    ]

    assert prompt_contains_all(
        prompt,
        grounding_concepts,
    )


def test_llm_report_generator_prompt_restricts_threshold_disclosure(
    analysis,
):
    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt.lower()

    assert "threshold" in prompt

    assert (
        "do not disclose" in prompt
        or "do not mention" in prompt
        or "do not reproduce" in prompt
    )


def test_llm_report_generator_prompt_excludes_status_generation(
    analysis,
):
    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt.lower()

    assert "do not generate an assessment status" in prompt
    assert "do not classify the assessment" in prompt
    assert "application will add" in prompt


# ============================================================
# Dynamic / non-hard-coded prompt content
# ============================================================


def test_llm_report_generator_prompt_supports_arbitrary_categories():
    findings = [
        make_analysis_finding(
            rule_id="CUSTOM_001",
            category="Custom Category A",
            severity=RuleSeverity.HIGH,
            text="Custom finding A.",
        ),
        make_analysis_finding(
            rule_id="CUSTOM_002",
            category="Custom Category B",
            severity=RuleSeverity.MEDIUM,
            text="Custom finding B.",
        ),
    ]

    analysis = make_analysis(
        key_findings=findings,
        risk_factors=[
            findings[0],
        ],
    )

    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt

    for finding in findings:
        assert finding.category in prompt
        assert finding.text in prompt


def test_llm_report_generator_prompt_supports_additional_findings_without_code_changes():
    findings = [
        make_analysis_finding(
            rule_id=f"DYNAMIC_{index}",
            category=f"Dynamic Category {index}",
            severity=RuleSeverity.MEDIUM,
            text=f"Dynamic finding {index}.",
        )
        for index in range(1, 6)
    ]

    analysis = make_analysis(
        key_findings=findings,
    )

    _, _, client = generate_report(
        analysis,
    )

    prompt = client.last_prompt

    for finding in findings:
        assert finding.rule_id in prompt
        assert finding.category in prompt
        assert finding.text in prompt


# ============================================================
# Valid responses
# ============================================================


def test_llm_report_generator_accepts_normal_narrative(
    analysis,
):
    response = (
        "Revenue and profitability indicators show "
        "material weaknesses."
    )

    _, report, _ = generate_report(
        analysis,
        response=response,
    )

    assert report.assessment_status == (
        analysis.assessment_status
    )

    assert response in report.executive_summary


def test_llm_report_generator_accepts_narrative_without_status(
    analysis,
):
    response = (
        "Revenue growth has declined and EBITDA remains "
        "negative, indicating financial weaknesses."
    )

    _, report, _ = generate_report(
        analysis,
        response=response,
    )

    assert report.executive_summary == (
        f"Assessment status: "
        f"{analysis.assessment_status.value}.\n"
        f"{response}"
    )


def test_llm_report_generator_does_not_require_status_in_llm_response(
    analysis,
):
    response = (
        "The company presents weaknesses in revenue "
        "growth and profitability."
    )

    _, report, _ = generate_report(
        analysis,
        response=response,
    )

    assert report.assessment_status == (
        analysis.assessment_status
    )

    assert response in report.executive_summary


# ============================================================
# Response validation
# ============================================================


def test_llm_report_generator_rejects_empty_response(
    analysis,
):
    client = MockLLMClient(
        response="",
    )

    generator = LLMReportGenerator(client)

    with pytest.raises(
        ValueError,
        match="LLM returned an empty response",
    ):
        generator.generate(analysis)


@pytest.mark.parametrize(
    "response",
    [
        " ",
        "\n",
        "\t",
        "   \n\t  ",
    ],
)
def test_llm_report_generator_rejects_whitespace_response(
    analysis,
    response,
):
    client = MockLLMClient(
        response=response,
    )

    generator = LLMReportGenerator(client)

    with pytest.raises(
        ValueError,
        match="LLM returned an empty response",
    ):
        generator.generate(analysis)


def test_llm_report_generator_accepts_multiple_status_words_in_narrative(
    analysis,
):
    """
    Status words appearing in the LLM narrative do not control
    the deterministic assessment status.

    The deterministic status remains authoritative.
    """

    response = (
        "The company is not classified as critical and the "
        "current findings should be monitored rather than "
        "treated as a normal financial position."
    )

    _, report, _ = generate_report(
        analysis,
        response=response,
    )

    assert report.assessment_status == (
        analysis.assessment_status
    )

    assert response in report.executive_summary


def test_llm_report_generator_propagates_client_errors(
    analysis,
):
    client = MagicMock(
        spec=LLMClient,
    )

    client.generate.side_effect = RuntimeError(
        "LLM service unavailable",
    )

    generator = LLMReportGenerator(client)

    with pytest.raises(
        RuntimeError,
        match="LLM service unavailable",
    ):
        generator.generate(analysis)

    client.generate.assert_called_once()


# ============================================================
# Structured data preservation
# ============================================================


def test_llm_report_generator_preserves_structured_data(
    analysis,
):
    _, report, _ = generate_report(
        analysis,
    )

    assert report.position_id == analysis.position_id

    assert report.assessment_status == (
        analysis.assessment_status
    )

    assert report.findings_by_category == (
        findings_by_category_from_analysis(
            analysis,
        )
    )

    assert report.limitations == (
        analysis.limitations
    )


def test_llm_report_generator_does_not_modify_analysis(
    analysis,
):
    original_key_findings = list(
        analysis.key_findings,
    )

    original_risk_factors = list(
        analysis.risk_factors,
    )

    original_limitations = list(
        analysis.limitations,
    )

    generate_report(
        analysis,
    )

    assert analysis.key_findings == (
        original_key_findings
    )

    assert analysis.risk_factors == (
        original_risk_factors
    )

    assert analysis.limitations == (
        original_limitations
    )


def test_llm_report_generator_does_not_use_generated_text_as_structured_data(
    analysis,
):
    injected_text = (
        "Generated content that does not exist "
        "in the deterministic analysis."
    )

    response = injected_text

    _, report, _ = generate_report(
        analysis,
        response=response,
    )

    structured_findings = report_findings(
        report,
    )

    assert structured_findings == (
        analysis.key_findings
    )

    assert report.limitations == (
        analysis.limitations
    )

    assert all(
        finding.text != injected_text
        for finding in structured_findings
    )


def test_llm_report_generator_preserves_finding_order(
    analysis,
):
    _, report, _ = generate_report(
        analysis,
    )

    assert report_findings(
        report,
    ) == analysis.key_findings


def test_llm_report_generator_preserves_categories(
    analysis,
):
    _, report, _ = generate_report(
        analysis,
    )

    expected_categories = [
        finding.category
        for finding in analysis.key_findings
    ]

    actual_categories = [
        finding.category
        for finding in report_findings(report)
    ]

    assert actual_categories == expected_categories


# ============================================================
# Category grouping
# ============================================================


def test_llm_report_generator_groups_findings_by_category(
    analysis,
):
    _, report, _ = generate_report(
        analysis,
    )

    grouped = report.findings_by_category

    categories = [
        group.category
        for group in grouped
    ]

    expected_categories = list(
        dict.fromkeys(
            finding.category
            for finding in analysis.key_findings
        )
    )

    assert categories == expected_categories


def test_llm_report_generator_keeps_findings_with_same_category_together(
    analysis,
):
    _, report, _ = generate_report(
        analysis,
    )

    profitability_groups = [
        group
        for group in report.findings_by_category
        if group.category == "Profitability"
    ]

    assert len(profitability_groups) == 1

    expected = [
        finding
        for finding in analysis.key_findings
        if finding.category == "Profitability"
    ]

    assert profitability_groups[0].findings == expected


# ============================================================
# Empty analysis
# ============================================================


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_llm_report_generator_supports_empty_analysis(
    status,
):
    analysis = make_analysis(
        status=status,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    _, report, client = generate_report(
        analysis,
    )

    assert report.position_id == analysis.position_id

    assert report.assessment_status == (
        analysis.assessment_status
    )

    expected_summary = (
        f"Assessment status: "
        f"{analysis.assessment_status.value}.\n"
        f"{client.response}"
    )

    assert report.executive_summary == (
        expected_summary
    )

    assert report.findings_by_category == []
    assert report.limitations == []


# ============================================================
# Client interaction
# ============================================================


def test_llm_report_generator_passes_prompt_to_client(
    analysis,
):
    client = MagicMock(
        spec=LLMClient,
    )

    client.generate.return_value = valid_response(
        analysis,
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

    client.generate.assert_called_once()

    prompt = client.generate.call_args.args[0]

    assert isinstance(
        prompt,
        str,
    )

    assert (
        analysis.assessment_status.value
        in prompt
    )


def test_llm_report_generator_uses_single_client_request(
    analysis,
):
    client = MagicMock(
        spec=LLMClient,
    )

    client.generate.return_value = valid_response(
        analysis,
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

    assert client.generate.call_count == 1