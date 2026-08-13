from unittest.mock import MagicMock

from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.llm.client import LLMClient
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
    llm_client.generate.return_value = "Generated summary"

    generator = LLMReportGenerator(llm_client)

    generator.generate(analysis)

    prompt = llm_client.generate.call_args.args[0]

    assert "CRITICAL" in prompt
    assert "Revenue Growth Deterioration" in prompt
    assert "Negative EBITDA" in prompt
    assert "High leverage" in prompt
    assert "Interest Coverage Ratio" in prompt