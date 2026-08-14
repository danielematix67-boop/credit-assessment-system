from unittest.mock import MagicMock

import pytest

from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.llm.client import LLMClient
from src.llm.mock_client import MockLLMClient
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report


def test_llm_report_generator_implements_report_generator_contract():

    llm_client = MagicMock(spec=LLMClient)

    report_generator = LLMReportGenerator(llm_client)

    assert isinstance(report_generator, LLMReportGenerator)


def test_llm_report_generator_uses_llm_client():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue deterioration detected.",
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "Negative EBITDA detected.",
        ],
        limitations=[
            "Interest Coverage Ratio could not be evaluated.",
        ],
    )

    llm_client = MagicMock(spec=LLMClient)

    llm_client.generate.return_value = (
        "The assessment indicates a CRITICAL credit position."
    )

    generator = LLMReportGenerator(llm_client)

    report = generator.generate(analysis)

    assert isinstance(report, Report)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status

    assert report.executive_summary == (
        "The assessment indicates a CRITICAL credit position."
    )

    # Structured findings remain deterministic.
    assert report.findings == analysis.key_findings

    # Structured limitations remain deterministic.
    assert report.limitations == analysis.limitations

    llm_client.generate.assert_called_once()


def test_llm_report_generator_builds_prompt_from_analysis():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue deterioration detected.",
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "High leverage detected.",
        ],
        limitations=[
            "Interest Coverage Ratio could not be evaluated.",
        ],
    )

    llm_client = MagicMock(spec=LLMClient)

    llm_client.generate.return_value = (
        "CRITICAL assessment identified."
    )

    generator = LLMReportGenerator(llm_client)

    generator.generate(analysis)

    prompt = llm_client.generate.call_args[0][0]

    assert "CRITICAL" in prompt

    # Findings originating from rule comments.
    assert "Revenue deterioration detected." in prompt
    assert "Negative EBITDA detected." in prompt

    # Risk factors originating from high-severity findings.
    assert "High leverage detected." in prompt

    # Limitations originating from not-evaluable findings.
    assert "Interest Coverage Ratio could not be evaluated." in prompt


def test_llm_report_generator_includes_analysis_in_prompt():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue deterioration detected.",
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "Negative EBITDA detected.",
        ],
        limitations=[
            "EBITDA Inventory Contribution could not be evaluated.",
        ],
    )

    client = MockLLMClient(
        response="CRITICAL assessment identified.",
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    generator.generate(analysis)

    prompt = client.last_prompt

    assert "CRITICAL" in prompt
    assert "Revenue deterioration detected." in prompt
    assert "Negative EBITDA detected." in prompt
    assert "EBITDA Inventory Contribution could not be evaluated." in prompt


def test_llm_report_generator_accepts_valid_response():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue deterioration detected.",
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "Negative EBITDA detected.",
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

    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations


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
            "Revenue deterioration detected.",
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "High leverage detected.",
        ],
        limitations=[
            "Interest Coverage Ratio could not be evaluated.",
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

    # The LLM cannot modify deterministic findings.
    assert report.findings == analysis.key_findings

    # The LLM cannot modify deterministic limitations.
    assert report.limitations == analysis.limitations

    assert report.executive_summary == (
        "CRITICAL assessment identified. "
        "The company has experienced revenue deterioration."
    )


def test_llm_report_generator_prompt_enforces_factual_constraints():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "High leverage detected.",
        ],
        limitations=[
            "Interest Coverage Ratio could not be evaluated.",
        ],
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
    assert "Do not modify the assessment status" in prompt
    assert "Do not make a credit decision" in prompt
    assert "Do not provide recommendations" in prompt
    assert "Clearly distinguish between findings and limitations" in prompt
    assert "If information is missing or not evaluable" in prompt
    assert "Generate only the executive summary" in prompt


def test_llm_report_generator_accepts_attention_status():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            "Revenue deterioration detected.",
        ],
        risk_factors=[
            "High leverage detected.",
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

    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations


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

    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations


def test_llm_report_generator_preserves_limitations():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            "Revenue deterioration detected.",
        ],
        risk_factors=[],
        limitations=[
            "Interest Coverage Ratio could not be evaluated.",
            "EBITDA Inventory Contribution could not be evaluated.",
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

    assert report.limitations == analysis.limitations
    assert report.findings == analysis.key_findings


def test_llm_report_generator_accepts_paraphrased_findings():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue deterioration detected.",
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "High leverage detected.",
        ],
        limitations=[],
    )

    client = MockLLMClient(
        response=(
            "CRITICAL assessment identified. "
            "The company experienced a deterioration in revenue "
            "and reported negative operating earnings."
        ),
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    report = generator.generate(analysis)

    # The LLM may paraphrase the comments in the executive summary.
    assert report.executive_summary == client.response

    # But the structured data remains deterministic.
    assert report.assessment_status == analysis.assessment_status
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations


def test_llm_report_generator_accepts_complete_response():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "Revenue deterioration detected.",
            "Negative EBITDA detected.",
        ],
        risk_factors=[
            "Negative EBITDA detected.",
        ],
        limitations=[
            "Interest Coverage Ratio could not be evaluated.",
        ],
    )

    client = MockLLMClient(
        response=(
            "CRITICAL assessment identified. "
            "The assessment shows revenue deterioration "
            "and negative EBITDA. "
            "Interest Coverage Ratio could not be evaluated."
        ),
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    report = generator.generate(analysis)

    assert report.executive_summary == client.response

    # Structured information is preserved independently
    # from the generated executive summary.
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations


def test_llm_report_generator_uses_comment_text_as_structured_input():

    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            "CUSTOM COMMENT: revenue deterioration detected.",
        ],
        risk_factors=[
            "CUSTOM COMMENT: revenue deterioration detected.",
        ],
        limitations=[
            "CUSTOM COMMENT: indicator could not be evaluated.",
        ],
    )

    client = MockLLMClient(
        response="CRITICAL assessment identified.",
    )

    generator = LLMReportGenerator(
        llm_client=client,
    )

    report = generator.generate(analysis)

    prompt = client.last_prompt

    # The reporting layer must use the structured analysis
    # produced by the AnalysisAgent, including comment text.
    assert "CUSTOM COMMENT: revenue deterioration detected." in prompt
    assert "CUSTOM COMMENT: indicator could not be evaluated." in prompt

    # The deterministic structured report data must also preserve it.
    assert report.findings == analysis.key_findings
    assert report.limitations == analysis.limitations