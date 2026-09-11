import pytest

from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.agents.reporting.deterministic_report_generator import DeterministicReportGenerator
from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.report_generator import ReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.agents.workflow.workflow_factory import create_default_assessment_workflow
from src.llm.mock_client import MockLLMClient
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_workflow import AssessmentWorkflowResult
from src.models.position import CreditPosition
from src.models.report import Report


@pytest.fixture
def representative_position():
    return CreditPosition(position_id="TEST_POSITION", revenue_growth=0.0, ebitda=1.0, profit_loss=1.0, ebitda_margin=0.0, nfp_to_ebitda=0.0, interest_expense=0.0)


@pytest.fixture
def llm_client():
    return MockLLMClient()


class FailingReportGenerator(ReportGenerator):
    def generate(self, analysis: AssessmentAnalysis) -> Report:
        raise RuntimeError("simulated report generation failure")


def test_factory_creates_default_workflow():
    workflow = create_default_assessment_workflow()
    assert isinstance(workflow, AssessmentWorkflow)
    assert isinstance(workflow.case_analysis_agent, CaseAnalysisAgent)
    assert isinstance(workflow.reporting_agent, ReportingAgent)
    assert isinstance(workflow.reporting_agent.report_generator, DeterministicReportGenerator)


def test_factory_always_wires_deterministic_fallback():
    deterministic_workflow = create_default_assessment_workflow(use_llm=False)
    llm_workflow = create_default_assessment_workflow(use_llm=True, llm_client=MockLLMClient())
    assert isinstance(deterministic_workflow.reporting_agent.fallback_generator, DeterministicReportGenerator)
    assert isinstance(llm_workflow.reporting_agent.fallback_generator, DeterministicReportGenerator)


def test_factory_creates_llm_workflow(llm_client):
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=llm_client)
    assert isinstance(workflow, AssessmentWorkflow)
    assert isinstance(workflow.case_analysis_agent, CaseAnalysisAgent)
    assert isinstance(workflow.reporting_agent, ReportingAgent)
    assert isinstance(workflow.reporting_agent.report_generator, LLMReportGenerator)


def test_factory_rejects_missing_llm_client_when_llm_enabled():
    with pytest.raises(ValueError, match="llm_client is required when use_llm=True"):
        create_default_assessment_workflow(use_llm=True)


@pytest.mark.parametrize("use_llm", [False, True])
def test_factory_creates_executable_workflow(representative_position, llm_client, use_llm):
    workflow = create_default_assessment_workflow(use_llm=use_llm, llm_client=llm_client if use_llm else None)
    result = workflow.run(representative_position)
    assert isinstance(result, AssessmentWorkflowResult)
    assert result.credit_case.position.position_id == representative_position.position_id
    assert result.analysis.position_id == representative_position.position_id
    assert result.report.position_id == representative_position.position_id
    assert result.analysis.assessment_status == result.credit_case.final_assessment.status
    assert result.report.assessment_status == result.credit_case.final_assessment.status


def test_factory_llm_workflow_falls_back_to_deterministic_report(representative_position):
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=MockLLMClient())
    workflow.reporting_agent.report_generator = FailingReportGenerator()
    result = workflow.run(representative_position)
    assert result.report.position_id == representative_position.position_id
    assert result.report.assessment_status == result.credit_case.final_assessment.status
    assert result.report.executive_summary
    assert result.execution_metadata is not None
    assert result.execution_metadata.generator_used == "FALLBACK"
    assert result.execution_metadata.fallback_used is True
    assert result.execution_metadata.error_category == "GENERATION_ERROR"


def test_factory_fallback_preserves_deterministic_findings(representative_position):
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=MockLLMClient())
    workflow.reporting_agent.report_generator = FailingReportGenerator()
    result = workflow.run(representative_position)
    expected_findings = sorted((f.rule_id, f.category, f.severity.value, f.text) for f in result.analysis.key_findings)
    fallback_findings = sorted((f.rule_id, f.category, f.severity.value, f.text) for group in result.report.findings_by_category for f in group.findings)
    assert fallback_findings == expected_findings
    assert result.analysis.assessment_status == result.report.assessment_status


def test_factory_does_not_create_findings_not_present_in_case(representative_position):
    workflow = create_default_assessment_workflow(use_llm=False)
    result = workflow.run(representative_position)
    case_rule_ids = {finding.result.rule_id for section in result.credit_case.sections for finding in section.findings}
    analysis_rule_ids = {finding.rule_id for finding in result.analysis.key_findings if finding.rule_id != "PROFILE"}
    assert analysis_rule_ids <= case_rule_ids


def test_llm_workflow_preserves_deterministic_assessment_data(representative_position, llm_client):
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=llm_client)
    result = workflow.run(representative_position)
    assert result.report.assessment_status == result.credit_case.final_assessment.status
    assert all(finding.rule_id for finding in result.analysis.key_findings)


def test_llm_workflow_preserves_assessment_status(representative_position, llm_client):
    workflow = create_default_assessment_workflow(use_llm=True, llm_client=llm_client)
    result = workflow.run(representative_position)
    assert result.analysis.assessment_status == result.credit_case.final_assessment.status
    assert result.report.assessment_status == result.credit_case.final_assessment.status


def test_factory_does_not_require_specific_rule_identifiers(representative_position):
    workflow = create_default_assessment_workflow(use_llm=False)
    result = workflow.run(representative_position)
    for finding in result.analysis.key_findings + result.analysis.risk_factors + result.analysis.limitations:
        assert finding.rule_id
