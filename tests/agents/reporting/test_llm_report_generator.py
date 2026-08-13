from unittest.mock import MagicMock
import pytest
from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.llm.client import LLMClient
from src.llm.mock_client import MockLLMClient
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report


def test_llm_report_generator_implements_report_generator_contract():

    generator = MagicMock(spec=LLMClient)

    report_generator = LLMReportGenerator(generator)

    assert isinstance(report_generator, LLMReportGenerator)


def test_llm_report_generator_uses_llm_client():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue Growth Deterioration",
            "Negative EBITDA",
        ],
        risk_factors=[
            "High leverage",
        ],
        limitations=[
            "Interest Coverage Ratio",
        ],
    )

    llm_client = MagicMock(spec=LLMClient)

    llm_client.generate.return_value = (
        "The assessment indicates a critical credit position."
    )

    generator = LLMReportGenerator(llm_client)

    report = generator.generate(analysis)

    assert isinstance(report, Report)

    assert report.position_id == "POS001"
    assert report.assessment_status == AssessmentStatus.CRITICAL

    assert (
        report.executive_summary
        == "The assessment indicates a critical credit position."
    )

    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations

    llm_client.generate.assert_called_once()

def test_llm_report_generator_builds_prompt_from_analysis():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue Growth Deterioration",
            "Negative EBITDA",
        ],
        risk_factors=[
            "High leverage",
        ],
        limitations=[
            "Interest Coverage Ratio",
        ],
    )

    llm_client = MagicMock(spec=LLMClient)
    llm_client.generate.return_value = (
        "CRITICAL assessment identified. Generated summary."
    )

    generator = LLMReportGenerator(llm_client)

    generator.generate(analysis)

    prompt = llm_client.generate.call_args[0][0]

    assert "CRITICAL" in prompt
    assert "Revenue Growth Deterioration" in prompt
    assert "Negative EBITDA" in prompt
    assert "High leverage" in prompt
    assert "Interest Coverage Ratio" in prompt


def test_llm_report_generator_includes_analysis_in_prompt():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue Growth",
            "Negative EBITDA",
        ],
        risk_factors=[
            "Negative EBITDA",
        ],
        limitations=[
            "EBITDA Inventory Contribution",
        ],
    )

    client = MockLLMClient()

    generator = LLMReportGenerator(
        llm_client=client,
    )

    generator.generate(analysis)

    prompt = client.last_prompt

    assert "CRITICAL" in prompt
    assert "Revenue Growth" in prompt
    assert "Negative EBITDA" in prompt
    assert "EBITDA Inventory Contribution" in prompt

def test_llm_report_generator_accepts_valid_response():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue Growth",
            "Negative EBITDA",
        ],
        risk_factors=[
            "Negative EBITDA",
        ],
        limitations=[],
    )

    client = MockLLMClient(
        response="CRITICAL assessment identified.",
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    report = generator.generate(analysis)

    assert report.executive_summary == (
        "CRITICAL assessment identified."
    )

def test_llm_report_generator_rejects_empty_response():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    client = MockLLMClient(
        response="",
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    with pytest.raises(
        ValueError,
        match="LLM returned an empty response",
    ):
        generator.generate(analysis)

def test_llm_report_generator_rejects_inconsistent_status():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    client = MockLLMClient(
        response="The assessment is NORMAL.",
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    with pytest.raises(
        ValueError,
        match="LLM response does not contain the assessment status",
    ):
        generator.generate(analysis)

def test_llm_report_generator_preserves_structured_assessment_data():
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue Growth",
            "Negative EBITDA",
        ],
        risk_factors=[
            "High Leverage",
        ],
        limitations=[
            "Interest Coverage Ratio",
        ],
    )

    client = MockLLMClient(
        response=(
            "CRITICAL assessment identified. "
            "The company has experienced revenue deterioration."
        ),
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations

    assert report.executive_summary == (
        "CRITICAL assessment identified. "
        "The company has experienced revenue deterioration."
    )

def test_llm_report_generator_prompt_enforces_factual_constraints():
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=["Negative EBITDA"],
        risk_factors=["High Leverage"],
        limitations=[],
    )

    client = MockLLMClient(
        response="CRITICAL assessment identified.",
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    generator.generate(analysis)

    prompt = client.last_prompt

    assert "EXCLUSIVELY" in prompt
    assert "Do not introduce facts" in prompt
    assert "Do not invent financial data" in prompt
    assert "Do not make a credit decision" in prompt
    assert "Generate only the executive summary" in prompt

def test_llm_report_generator_accepts_attention_status():
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            "Revenue Growth Deterioration",
        ],
        risk_factors=[
            "High Leverage",
        ],
        limitations=[],
    )

    client = MockLLMClient(
        response="ATTENTION assessment identified.",
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    report = generator.generate(analysis)

    assert report.assessment_status == AssessmentStatus.ATTENTION
    assert report.executive_summary == (
        "ATTENTION assessment identified."
    )


def test_llm_report_generator_accepts_normal_status():
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.NORMAL,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    client = MockLLMClient(
        response="NORMAL assessment. No critical issues identified.",
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    report = generator.generate(analysis)

    assert report.assessment_status == AssessmentStatus.NORMAL
    assert report.executive_summary == (
        "NORMAL assessment. No critical issues identified."
    )


def test_llm_report_generator_preserves_limitations():
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            "Revenue Growth Deterioration",
        ],
        risk_factors=[],
        limitations=[
            "Interest Coverage Ratio",
            "EBITDA Inventory Contribution",
        ],
    )

    client = MockLLMClient(
        response=(
            "ATTENTION assessment identified. "
            "Some indicators could not be evaluated."
        ),
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    report = generator.generate(analysis)

    assert report.assessment_status == AssessmentStatus.ATTENTION

    assert report.limitations == [
        "Interest Coverage Ratio",
        "EBITDA Inventory Contribution",
    ]