from unittest.mock import MagicMock

import pytest

from src.agents.reporting.llm_report_generator import (
    LLMReportGenerator,
)
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


@pytest.fixture
def critical_analysis():
    return AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            AnalysisFinding(
                rule_id="R001",
                category="revenue",
                severity=RuleSeverity.MEDIUM,
                text="Revenue deterioration detected.",
            ),
            AnalysisFinding(
                rule_id="R002",
                category="profitability",
                severity=RuleSeverity.HIGH,
                text="Negative EBITDA detected.",
            ),
        ],
        risk_factors=[
            AnalysisFinding(
                rule_id="R002",
                category="profitability",
                severity=RuleSeverity.HIGH,
                text="Negative EBITDA detected.",
            ),
        ],
        limitations=[
            AnalysisFinding(
                rule_id="R005",
                category="profitability",
                severity=RuleSeverity.MEDIUM,
                text=(
                    "Interest expense to EBITDA "
                    "could not be evaluated."
                ),
            ),
        ],
    )


@pytest.fixture
def attention_analysis():
    return AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            AnalysisFinding(
                rule_id="R001",
                category="revenue",
                severity=RuleSeverity.MEDIUM,
                text="Revenue deterioration detected.",
            ),
        ],
        risk_factors=[],
        limitations=[],
    )


@pytest.fixture
def normal_analysis():
    return AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=AssessmentStatus.NORMAL,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )


# ============================================================
# Helpers
# ============================================================


def findings_by_category_from_analysis(analysis):
    categories = {}

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


# ============================================================
# Contract and basic generation
# ============================================================


def test_llm_report_generator_implements_report_generator_contract():
    client = MagicMock(spec=LLMClient)

    generator = LLMReportGenerator(client)

    assert isinstance(generator, LLMReportGenerator)


def test_llm_report_generator_uses_llm_client(
    critical_analysis,
):
    response = (
        f"{critical_analysis.assessment_status.value} "
        "assessment identified."
    )

    client = MagicMock(spec=LLMClient)
    client.generate.return_value = response

    generator = LLMReportGenerator(client)

    report = generator.generate(critical_analysis)

    assert isinstance(report, Report)

    assert report.position_id == critical_analysis.position_id

    assert report.assessment_status == (
        critical_analysis.assessment_status
    )

    assert report.executive_summary == response

    assert report.findings_by_category == (
        findings_by_category_from_analysis(
            critical_analysis
        )
    )

    assert report.limitations == (
        critical_analysis.limitations
    )

    client.generate.assert_called_once()


# ============================================================
# Prompt construction
# ============================================================


def test_llm_report_generator_builds_prompt_from_analysis(
    critical_analysis,
):
    client = MockLLMClient(
        response=(
            f"{critical_analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    generator.generate(critical_analysis)

    prompt = client.last_prompt

    assert critical_analysis.assessment_status.value in prompt

    expected_content = (
        critical_analysis.key_findings
        + critical_analysis.risk_factors
        + critical_analysis.limitations
    )

    for finding in expected_content:
        assert finding.text in prompt


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_llm_report_generator_includes_assessment_status_in_prompt(
    status,
):
    analysis = AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=status,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    client = MockLLMClient(
        response=f"{status.value} assessment identified.",
    )

    generator = LLMReportGenerator(client)

    generator.generate(analysis)

    assert (
        f"Assessment status: {status.value}"
        in client.last_prompt
    )


def test_llm_report_generator_prompt_contains_all_structured_sections(
    critical_analysis,
):
    client = MockLLMClient(
        response=(
            f"{critical_analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    generator.generate(critical_analysis)

    prompt = client.last_prompt

    # The prompt must expose the three structured
    # sections used by the reporting agent.
    assert "Key findings:" in prompt
    assert "Risk factors:" in prompt
    assert "Limitations:" in prompt

    # Assessment status must be explicitly provided.
    assert (
        f"Assessment status: "
        f"{critical_analysis.assessment_status.value}"
        in prompt
    )

    # Every key finding must be available to the LLM.
    for finding in critical_analysis.key_findings:
        assert finding.rule_id in prompt
        assert finding.category in prompt
        assert finding.severity.value in prompt
        assert finding.text in prompt

    # Every risk factor must be available to the LLM.
    for risk in critical_analysis.risk_factors:
        assert risk.rule_id in prompt
        assert risk.category in prompt
        assert risk.severity.value in prompt
        assert risk.text in prompt

    # Every limitation must be available to the LLM.
    for limitation in critical_analysis.limitations:
        assert limitation.rule_id in prompt
        assert limitation.category in prompt
        assert limitation.severity.value in prompt
        assert limitation.text in prompt


def test_llm_report_generator_prompt_enforces_factual_constraints(
    critical_analysis,
):
    client = MockLLMClient(
        response=(
            f"{critical_analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    generator.generate(critical_analysis)

    prompt = client.last_prompt

    expected_constraints = [
        "EXCLUSIVELY",
        "Do not introduce facts",
        "Do not invent financial data",
        "Do not modify the assessment status",
        "Do not make a credit decision",
        "Do not provide recommendations",
        "Clearly distinguish between findings and limitations",
        "If information is missing or not evaluable",
        "Generate only the executive summary",
    ]

    for constraint in expected_constraints:
        assert constraint in prompt


def test_llm_report_generator_uses_analysis_as_structured_input(
    critical_analysis,
):
    client = MockLLMClient(
        response=(
            f"{critical_analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(critical_analysis)

    prompt = client.last_prompt

    expected_content = (
        critical_analysis.key_findings
        + critical_analysis.risk_factors
        + critical_analysis.limitations
    )

    for finding in expected_content:
        assert finding.text in prompt

    # Structured report data remains deterministic.
    assert report.findings_by_category == (
        findings_by_category_from_analysis(
            critical_analysis
        )
    )

    assert report.limitations == (
        critical_analysis.limitations
    )


# ============================================================
# Valid assessment statuses
# ============================================================


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_llm_report_generator_accepts_valid_assessment_status(
    status,
):
    analysis = AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=status,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    response = f"{status.value} assessment identified."

    client = MockLLMClient(response=response)

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert report.assessment_status == status
    assert report.executive_summary == response
    assert report.findings_by_category == []
    assert report.limitations == []


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_llm_report_generator_rejects_inconsistent_status(
    status,
):
    analysis = AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=status,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

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


# ============================================================
# Response validation
# ============================================================


def test_llm_report_generator_accepts_valid_response(
    critical_analysis,
):
    client = MockLLMClient(
        response=(
            f"{critical_analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(critical_analysis)

    assert report.executive_summary == client.response

    assert report.findings_by_category == (
        findings_by_category_from_analysis(
            critical_analysis
        )
    )

    assert report.limitations == (
        critical_analysis.limitations
    )


def test_llm_report_generator_accepts_paraphrased_findings(
    critical_analysis,
):
    response = (
        f"{critical_analysis.assessment_status.value} "
        "assessment identified. "
        "The assessment contains a number of "
        "relevant observations."
    )

    client = MockLLMClient(response=response)

    generator = LLMReportGenerator(client)

    report = generator.generate(critical_analysis)

    # The LLM may paraphrase the executive summary.
    assert report.executive_summary == client.response

    # Structured information remains deterministic.
    assert report.assessment_status == (
        critical_analysis.assessment_status
    )

    assert report.findings_by_category == (
        findings_by_category_from_analysis(
            critical_analysis
        )
    )

    assert report.limitations == (
        critical_analysis.limitations
    )


def test_llm_report_generator_accepts_complete_response(
    critical_analysis,
):
    response = (
        f"{critical_analysis.assessment_status.value} "
        "assessment identified. "
        "The assessment contains several relevant findings. "
        "Some information could not be evaluated."
    )

    client = MockLLMClient(response=response)

    generator = LLMReportGenerator(client)

    report = generator.generate(critical_analysis)

    assert report.executive_summary == client.response

    # Structured information is preserved independently
    # from the generated executive summary.
    assert report.findings_by_category == (
        findings_by_category_from_analysis(
            critical_analysis
        )
    )

    assert report.limitations == (
        critical_analysis.limitations
    )


def test_llm_report_generator_rejects_empty_response(
    critical_analysis,
):
    client = MockLLMClient(response="")

    generator = LLMReportGenerator(client)

    with pytest.raises(
        ValueError,
        match="LLM returned an empty response",
    ):
        generator.generate(critical_analysis)


@pytest.mark.parametrize(
    "response",
    [
        "   ",
        "\n",
        "\t",
    ],
)
def test_llm_report_generator_rejects_whitespace_only_response(
    critical_analysis,
    response,
):
    client = MockLLMClient(response=response)

    generator = LLMReportGenerator(client)

    with pytest.raises(
        ValueError,
        match="LLM returned an empty response",
    ):
        generator.generate(critical_analysis)


def test_llm_report_generator_propagates_llm_client_errors(
    critical_analysis,
):
    client = MagicMock(spec=LLMClient)

    client.generate.side_effect = RuntimeError(
        "Gemini API unavailable"
    )

    generator = LLMReportGenerator(client)

    with pytest.raises(
        RuntimeError,
        match="Gemini API unavailable",
    ):
        generator.generate(critical_analysis)

    client.generate.assert_called_once()


# ============================================================
# Structured data preservation
# ============================================================


@pytest.mark.parametrize(
    "analysis_fixture",
    [
        "critical_analysis",
        "attention_analysis",
        "normal_analysis",
    ],
)
def test_llm_report_generator_preserves_structured_assessment_data(
    request,
    analysis_fixture,
):
    analysis = request.getfixturevalue(
        analysis_fixture
    )

    client = MockLLMClient(
        response=(
            f"{analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == (
        analysis.assessment_status
    )

    # Findings remain deterministic and structured.
    assert report.findings_by_category == (
        findings_by_category_from_analysis(
            analysis
        )
    )

    # Limitations remain deterministic and structured.
    assert report.limitations == (
        analysis.limitations
    )

    assert report.executive_summary == client.response


def test_llm_report_generator_preserves_limitations(
    attention_analysis,
):
    client = MockLLMClient(
        response=(
            f"{attention_analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(attention_analysis)

    assert report.assessment_status == (
        attention_analysis.assessment_status
    )

    assert report.limitations == (
        attention_analysis.limitations
    )

    assert report.findings_by_category == (
        findings_by_category_from_analysis(
            attention_analysis
        )
    )


@pytest.mark.parametrize(
    "analysis_fixture",
    [
        "critical_analysis",
        "attention_analysis",
        "normal_analysis",
    ],
)
def test_llm_report_generator_preserves_position_and_status(
    request,
    analysis_fixture,
):
    analysis = request.getfixturevalue(
        analysis_fixture
    )

    client = MockLLMClient(
        response=(
            f"{analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == (
        analysis.assessment_status
    )


def test_llm_report_generator_does_not_modify_analysis(
    critical_analysis,
):
    original_key_findings = list(
        critical_analysis.key_findings
    )
    original_risk_factors = list(
        critical_analysis.risk_factors
    )
    original_limitations = list(
        critical_analysis.limitations
    )

    client = MockLLMClient(
        response=(
            f"{critical_analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    generator.generate(critical_analysis)

    assert (
        critical_analysis.key_findings
        == original_key_findings
    )

    assert (
        critical_analysis.risk_factors
        == original_risk_factors
    )

    assert (
        critical_analysis.limitations
        == original_limitations
    )


def test_llm_report_generator_does_not_use_llm_response_as_structured_data(
    critical_analysis,
):
    client = MockLLMClient(
        response=(
            f"{critical_analysis.assessment_status.value} "
            "assessment identified. "
            "Invented finding that does not exist "
            "in the analysis."
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(critical_analysis)

    report_findings = [
        finding
        for group in report.findings_by_category
        for finding in group.findings
    ]

    assert report_findings == (
        critical_analysis.key_findings
    )

    assert report.limitations == (
        critical_analysis.limitations
    )

    assert all(
        finding.text
        != (
            "Invented finding that does not exist "
            "in the analysis."
        )
        for finding in report_findings
    )


def test_llm_report_generator_preserves_finding_order_within_categories(
    critical_analysis,
):
    client = MockLLMClient(
        response=(
            f"{critical_analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(critical_analysis)

    report_findings = [
        finding
        for group in report.findings_by_category
        for finding in group.findings
    ]

    assert report_findings == (
        critical_analysis.key_findings
    )


# ============================================================
# Empty analysis
# ============================================================


def test_llm_report_generator_supports_empty_analysis(
    normal_analysis,
):
    client = MockLLMClient(
        response=(
            f"{normal_analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(normal_analysis)

    assert report.position_id == (
        normal_analysis.position_id
    )

    assert report.assessment_status == (
        normal_analysis.assessment_status
    )

    assert report.executive_summary == client.response

    assert report.findings_by_category == []

    assert report.limitations == []
