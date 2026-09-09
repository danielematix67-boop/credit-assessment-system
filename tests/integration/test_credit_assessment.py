import pytest

from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.workflow.workflow_factory import create_default_assessment_workflow
from src.llm.mock_client import MockLLMClient
from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus


@pytest.fixture
def risk_position() -> CreditPosition:
    return CreditPosition(
        position_id="TEST_POSITION",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        nfp_to_ebitda=6.0,
        interest_expense=40000,
    )


@pytest.fixture
def normal_position() -> CreditPosition:
    return CreditPosition(
        position_id="TEST_NORMAL_POSITION",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=100000,
        ebitda_margin=0.15,
        nfp_to_ebitda=2.0,
        interest_expense=10000,
    )


def report_findings_by_category(report):
    return {group.category: group.findings for group in report.findings_by_category}


def analysis_findings_by_category(analysis):
    grouped = {}
    for finding in analysis.key_findings:
        grouped.setdefault(finding.category, []).append(finding)
    return grouped


def deterministic_findings(assessment):
    return [
        finding
        for finding in assessment.findings
        if finding.result.status == RuleStatus.TRIGGERED
    ]


def normalize_prompt(prompt: str) -> str:
    return " ".join(prompt.lower().split())


def assert_prompt_contains_any(prompt: str, alternatives: tuple[str, ...]) -> None:
    normalized = normalize_prompt(prompt)
    assert any(option.lower() in normalized for option in alternatives)


def assert_deterministic_information_is_preserved(result):
    assert result.assessment is not None
    assert result.analysis is not None
    assert result.report is not None
    assert result.analysis.assessment_status == result.assessment.status
    assert result.report.assessment_status == result.assessment.status
    assert report_findings_by_category(result.report) == analysis_findings_by_category(
        result.analysis
    )
    assert result.report.limitations == result.analysis.limitations


def make_valid_llm_response():
    return (
        "The analysis highlights relevant financial risk factors affecting the company's "
        "credit profile. The observed indicators suggest areas requiring continuous monitoring."
    )


def test_credit_assessment_end_to_end(risk_position):
    workflow = create_default_assessment_workflow(use_llm=False)
    result = workflow.run(risk_position)
    assert result.assessment.position_id == risk_position.position_id
    assert result.analysis.position_id == risk_position.position_id
    assert result.report.position_id == risk_position.position_id
    assert result.report.assessment_status == result.assessment.status
    assert result.report.executive_summary
    assert isinstance(result.report.limitations, list)


def test_credit_assessment_propagates_findings_through_pipeline(risk_position):
    result = create_default_assessment_workflow(use_llm=False).run(risk_position)
    triggered = deterministic_findings(result.assessment)
    expected = [(f.result.category, f.comment.text) for f in triggered]
    actual = [(f.category, f.text) for f in result.analysis.key_findings]
    assert triggered
    assert result.assessment.findings
    assert actual == expected
    assert report_findings_by_category(result.report) == analysis_findings_by_category(
        result.analysis
    )
    assert result.report.limitations == result.analysis.limitations


def test_llm_workflow_uses_primary_generator(risk_position):
    client = MockLLMClient(response=make_valid_llm_response())
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=client)
    assert isinstance(workflow.reporting_agent.report_generator, LLMReportGenerator)
    result = workflow.run(risk_position)
    assert result.report.executive_summary
    assert workflow.reporting_agent.last_generator_used == "PRIMARY"
    assert workflow.reporting_agent.last_error is None


def test_credit_assessment_llm_workflow(risk_position):
    client = MockLLMClient(response=make_valid_llm_response())
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=client)
    result = workflow.run(risk_position)
    assert_deterministic_information_is_preserved(result)
    assert workflow.reporting_agent.last_generator_used == "PRIMARY"
    assert workflow.reporting_agent.last_error is None


def test_llm_workflow_sends_prompt_to_llm_client(risk_position):
    client = MockLLMClient(response=make_valid_llm_response())
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=client)
    workflow.run(risk_position)
    assert client.last_prompt is not None
    assert client.last_prompt.strip()


def test_llm_prompt_contains_deterministic_assessment_data(risk_position):
    deterministic = create_default_assessment_workflow(use_llm=False).run(risk_position)
    client = MockLLMClient(response=make_valid_llm_response())
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=client)
    workflow.run(risk_position)
    assert client.last_prompt is not None
    normalized = normalize_prompt(client.last_prompt)
    for finding in deterministic.analysis.key_findings:
        assert finding.text.lower() in normalized
    for finding in deterministic.analysis.risk_factors:
        assert finding.text.lower() in normalized


def test_llm_prompt_contains_safety_constraints(risk_position):
    client = MockLLMClient(response=make_valid_llm_response())
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=client)
    workflow.run(risk_position)
    prompt = client.last_prompt
    assert prompt is not None
    assert_prompt_contains_any(prompt, ("deterministic assessment", "rule-based assessment"))
    assert_prompt_contains_any(prompt, ("only", "exclusively", "solely"))
    assert_prompt_contains_any(prompt, ("do not invent", "do not fabricate", "do not add facts"))
    assert_prompt_contains_any(prompt, ("do not modify", "do not alter", "do not override"))


def test_llm_cannot_change_deterministic_assessment(risk_position):
    expected = create_default_assessment_workflow(use_llm=False).run(risk_position).assessment.status
    client = MockLLMClient(response="The company shows severe financial deterioration.")
    result = create_default_assessment_workflow(use_llm=True, llm_client=client).run(risk_position)
    assert result.assessment.status == expected
    assert result.analysis.assessment_status == expected
    assert result.report.assessment_status == expected
    assert_deterministic_information_is_preserved(result)


def test_llm_cannot_replace_deterministic_findings(risk_position):
    client = MockLLMClient(response="The company has a strong financial profile.")
    result = create_default_assessment_workflow(use_llm=True, llm_client=client).run(risk_position)
    assert report_findings_by_category(result.report) == analysis_findings_by_category(result.analysis)
    report_text = [item.text for group in result.report.findings_by_category for item in group.findings]
    assert all(finding.text in report_text for finding in result.analysis.key_findings)


def test_llm_cannot_replace_deterministic_limitations(risk_position):
    client = MockLLMClient(response="All available information has been summarized.")
    result = create_default_assessment_workflow(use_llm=True, llm_client=client).run(risk_position)
    assert result.report.limitations == result.analysis.limitations


def test_llm_response_is_rejected_when_empty(risk_position):
    client = MockLLMClient(response="   ")
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=client)
    result = workflow.run(risk_position)
    assert result.report is not None
    assert workflow.reporting_agent.last_generator_used == "FALLBACK"
    assert workflow.reporting_agent.last_error == "LLM report generation failed: LLM returned an empty response"
    assert result.report.assessment_status == result.assessment.status


def test_llm_response_content_is_preserved(risk_position):
    response = "This narrative was generated by the LLM to summarize the available information."
    client = MockLLMClient(response=response)
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=client)
    result = workflow.run(risk_position)
    assert workflow.reporting_agent.last_generator_used == "PRIMARY"
    assert response in result.report.executive_summary
    assert result.report.executive_summary.startswith("Assessment Status:")


def test_llm_response_whitespace_is_normalized(risk_position):
    response = "   Generated narrative content with surrounding spaces.   "
    client = MockLLMClient(response=response)
    result = create_default_assessment_workflow(use_llm=True, llm_client=client).run(risk_position)
    assert "Generated narrative content with surrounding spaces." in result.report.executive_summary
    assert result.report.executive_summary.startswith("Assessment Status:")


def test_llm_accepts_response_without_assessment_status(risk_position):
    response = "The generated narrative focuses on financial indicators and relevant observations."
    client = MockLLMClient(response=response)
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=client)
    result = workflow.run(risk_position)
    assert workflow.reporting_agent.last_generator_used == "PRIMARY"
    assert workflow.reporting_agent.last_error is None
    assert response in result.report.executive_summary
    assert result.report.executive_summary.startswith("Assessment Status:")


def test_credit_assessment_falls_back_to_deterministic_report_when_llm_fails(risk_position):
    client = MockLLMClient(error=RuntimeError("LLM service unavailable"))
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=client)
    result = workflow.run(risk_position)
    assert result.assessment.status == result.analysis.assessment_status
    assert result.report.assessment_status == result.assessment.status
    assert result.report.executive_summary
    assert workflow.reporting_agent.last_generator_used == "FALLBACK"
    assert workflow.reporting_agent.last_error == "LLM service is temporarily unavailable."
    assert_deterministic_information_is_preserved(result)


def test_not_evaluable_rules_do_not_generate_findings(normal_position):
    result = create_default_assessment_workflow(use_llm=False).run(normal_position)
    not_evaluable = [
        rule_result
        for rule_result in result.assessment.rule_results
        if rule_result.status == RuleStatus.NOT_EVALUABLE
    ]
    assert not_evaluable
    not_evaluable_ids = {item.rule_id for item in not_evaluable}
    finding_ids = {finding.result.rule_id for finding in result.assessment.findings}
    assert finding_ids.isdisjoint(not_evaluable_ids)
    assert result.analysis.key_findings == []
    assert report_findings_by_category(result.report) == {}
