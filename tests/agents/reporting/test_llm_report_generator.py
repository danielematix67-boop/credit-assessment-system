from unittest.mock import MagicMock

import pytest

from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.llm.client import LLMClient
from src.llm.mock_client import MockLLMClient
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report


@pytest.fixture
def critical_analysis():
    return AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Finding A",
            "Finding B",
        ],
        risk_factors=[
            "Risk A",
        ],
        limitations=[
            "Limitation A",
        ],
    )


@pytest.fixture
def attention_analysis():
    return AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            "Finding A",
        ],
        risk_factors=[
            "Risk A",
        ],
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


@pytest.fixture
def analyses(
    critical_analysis,
    attention_analysis,
    normal_analysis,
):
    return [
        critical_analysis,
        attention_analysis,
        normal_analysis,
    ]


def test_llm_report_generator_implements_report_generator_contract():
    client = MagicMock(spec=LLMClient)

    generator = LLMReportGenerator(client)

    assert isinstance(generator, LLMReportGenerator)


def test_llm_report_generator_uses_llm_client(critical_analysis):
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

    # Structured information remains deterministic.
    assert report.findings == critical_analysis.key_findings
    assert report.limitations == critical_analysis.limitations

    client.generate.assert_called_once()


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

    for item in expected_content:
        assert item in prompt


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

    assert status.value in client.last_prompt


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
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations


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
    assert report.findings == critical_analysis.key_findings
    assert report.limitations == critical_analysis.limitations


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
    "status",
    list(AssessmentStatus),
)
def test_llm_report_generator_rejects_inconsistent_status(status):
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
        pytest.skip("No inconsistent status available.")

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
        match="LLM response does not contain the assessment status",
    ):
        generator.generate(analysis)


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
    analysis = request.getfixturevalue(analysis_fixture)

    client = MockLLMClient(
        response=(
            f"{analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status

    # The LLM cannot modify deterministic findings.
    assert report.findings == analysis.key_findings

    # The LLM cannot modify deterministic limitations.
    assert report.limitations == analysis.limitations

    assert report.executive_summary == client.response


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
    assert report.limitations == attention_analysis.limitations
    assert report.findings == attention_analysis.key_findings


def test_llm_report_generator_accepts_paraphrased_findings(
    critical_analysis,
):
    response = (
        f"{critical_analysis.assessment_status.value} "
        "assessment identified. "
        "The assessment contains a number of relevant observations."
    )

    client = MockLLMClient(response=response)

    generator = LLMReportGenerator(client)

    report = generator.generate(critical_analysis)

    # The LLM may paraphrase the deterministic analysis.
    assert report.executive_summary == client.response

    # Structured information remains deterministic.
    assert report.assessment_status == (
        critical_analysis.assessment_status
    )
    assert report.findings == critical_analysis.key_findings
    assert report.limitations == critical_analysis.limitations


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
    assert report.findings == critical_analysis.key_findings
    assert report.limitations == critical_analysis.limitations


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

    for item in expected_content:
        assert item in prompt

    # Deterministic structured report data must be preserved.
    assert report.findings == critical_analysis.key_findings
    assert report.limitations == critical_analysis.limitations


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
    analysis = request.getfixturevalue(analysis_fixture)

    client = MockLLMClient(
        response=(
            f"{analysis.assessment_status.value} "
            "assessment identified."
        ),
    )

    generator = LLMReportGenerator(client)

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status