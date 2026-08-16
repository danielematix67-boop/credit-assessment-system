from unittest.mock import MagicMock

import pytest

from src.agents.reporting.llm_report_generator import (
    LLMReportGenerator,
)
from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.llm.mock_client import MockLLMClient
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report, ReportFindingGroup
from src.rules.base.severity import RuleSeverity


# ============================================================
# Fixtures
# ============================================================


def make_analysis_finding(
    *,
    rule_id: str = "TEST_RULE",
    category: str = "test_category",
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
def analysis():
    findings = [
        make_analysis_finding(
            rule_id=f"RULE_{index}",
            category=f"category_{index}",
            severity=severity,
            text=f"Finding {index}.",
        )
        for index, severity in enumerate(
            RuleSeverity,
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
            rule_id="LIMITATION_RULE",
            category="limitation_category",
            severity=RuleSeverity.MEDIUM,
            text="Test limitation.",
        ),
    ]

    return make_analysis(
        position_id="TEST_POSITION",
        status=AssessmentStatus.ATTENTION,
        key_findings=findings,
        risk_factors=risk_factors,
        limitations=limitations,
    )


@pytest.fixture
def generator():
    return LLMReportGenerator(
        MockLLMClient(
            response=(
                f"{AssessmentStatus.ATTENTION.value} "
                "assessment identified."
            ),
        ),
    )


# ============================================================
# Helpers
# ============================================================


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


def valid_response(
    analysis: AssessmentAnalysis,
) -> str:
    return (
        f"{analysis.assessment_status.value} "
        "assessment identified."
    )


# ============================================================
# Contract
# ============================================================


def test_llm_report_generator_implements_report_generator_contract(
    generator,
):
    assert isinstance(generator, ReportGenerator)


# ============================================================
# Basic generation
# ============================================================


def test_llm_report_generator_generates_report(
    analysis,
):
    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert isinstance(report, Report)
    assert report.position_id == analysis.position_id
    assert report.assessment_status == (
        analysis.assessment_status
    )
    assert report.executive_summary == client.response


def test_llm_report_generator_invokes_llm_client(
    analysis,
):
    client = MagicMock(spec=LLMClient)
    client.generate.return_value = valid_response(
        analysis
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

    client.generate.assert_called_once()


# ============================================================
# Prompt construction
# ============================================================


def test_llm_report_generator_builds_prompt_from_analysis(
    analysis,
):
    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

    prompt = client.last_prompt

    assert (
        analysis.assessment_status.value
        in prompt
    )

    for finding in (
        analysis.key_findings
        + analysis.risk_factors
        + analysis.limitations
    ):
        assert finding.rule_id in prompt
        assert finding.category in prompt
        assert finding.severity.value in prompt
        assert finding.text in prompt


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_llm_report_generator_includes_status_in_prompt(
    status,
):
    analysis = make_analysis(status=status)

    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

    assert (
        f"Assessment status: {status.value}"
        in client.last_prompt
    )


def test_llm_report_generator_includes_structured_sections(
    analysis,
):
    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

    prompt = client.last_prompt

    assert "Key findings:" in prompt
    assert "Risk factors:" in prompt
    assert "Limitations:" in prompt


def test_llm_report_generator_includes_all_analysis_content(
    analysis,
):
    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

    prompt = client.last_prompt

    expected_findings = (
        analysis.key_findings
        + analysis.risk_factors
        + analysis.limitations
    )

    for finding in expected_findings:
        assert finding.text in prompt


def test_llm_report_generator_prompt_contains_reporting_constraints(
    analysis,
):
    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

    prompt = client.last_prompt

    expected_constraints = [
        "EXCLUSIVELY",
        "Do not introduce facts",
        "Do not invent financial data",
        "Do not modify the assessment status",
        "Do not make a credit decision",
        "Do not provide recommendations",
        "Clearly distinguish between findings and limitations",
        "Generate only the executive summary",
    ]

    for constraint in expected_constraints:
        assert constraint in prompt


# ============================================================
# Valid responses
# ============================================================


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_llm_report_generator_accepts_all_valid_statuses(
    status,
):
    analysis = make_analysis(status=status)

    response = valid_response(analysis)

    client = MockLLMClient(response=response)

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert report.assessment_status == status
    assert report.executive_summary == response


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_llm_report_generator_rejects_inconsistent_status(
    status,
):
    analysis = make_analysis(status=status)

    inconsistent_statuses = [
        candidate
        for candidate in AssessmentStatus
        if candidate != status
    ]

    if not inconsistent_statuses:
        pytest.skip(
            "No inconsistent status available."
        )

    inconsistent_status = inconsistent_statuses[0]

    client = MockLLMClient(
        response=(
            f"The assessment is "
            f"{inconsistent_status.value}."
        ),
    )

    generator = LLMReportGenerator(client)

    with pytest.raises(
        ValueError,
        match=(
            "LLM response does not contain "
            "the assessment status"
        ),
    ):
        generator.generate(analysis)


def test_llm_report_generator_accepts_paraphrased_response(
    analysis,
):
    response = (
        f"The overall classification is "
        f"{analysis.assessment_status.value}. "
        "The assessment contains relevant observations."
    )

    client = MockLLMClient(response=response)

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert report.executive_summary == response
    assert report.assessment_status == (
        analysis.assessment_status
    )


# ============================================================
# Response validation
# ============================================================


def test_llm_report_generator_rejects_empty_response(
    analysis,
):
    client = MockLLMClient(response="")

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
    client = MockLLMClient(response=response)

    generator = LLMReportGenerator(client)

    with pytest.raises(
        ValueError,
        match="LLM returned an empty response",
    ):
        generator.generate(analysis)


def test_llm_report_generator_propagates_client_errors(
    analysis,
):
    client = MagicMock(spec=LLMClient)

    client.generate.side_effect = RuntimeError(
        "LLM service unavailable"
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
    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id

    assert report.assessment_status == (
        analysis.assessment_status
    )

    assert report.findings_by_category == (
        findings_by_category_from_analysis(analysis)
    )

    assert report.limitations == (
        analysis.limitations
    )


def test_llm_report_generator_does_not_modify_analysis(
    analysis,
):
    original_key_findings = list(
        analysis.key_findings
    )
    original_risk_factors = list(
        analysis.risk_factors
    )
    original_limitations = list(
        analysis.limitations
    )

    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

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

    response = (
        f"{valid_response(analysis)} "
        f"{injected_text}"
    )

    client = MockLLMClient(response=response)

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    report_findings = [
        finding
        for group in report.findings_by_category
        for finding in group.findings
    ]

    assert report_findings == (
        analysis.key_findings
    )

    assert report.limitations == (
        analysis.limitations
    )

    assert all(
        finding.text != injected_text
        for finding in report_findings
    )


def test_llm_report_generator_preserves_finding_order(
    analysis,
):
    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    report_findings = [
        finding
        for group in report.findings_by_category
        for finding in group.findings
    ]

    assert report_findings == (
        analysis.key_findings
    )


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

    client = MockLLMClient(
        response=valid_response(analysis),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert report.position_id == (
        analysis.position_id
    )

    assert report.assessment_status == (
        analysis.assessment_status
    )

    assert report.executive_summary == (
        client.response
    )

    assert report.findings_by_category == []
    assert report.limitations == []