from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.agents.workflow.workflow_factory import (
    create_default_assessment_workflow,
)


def test_default_workflow_factory_creates_valid_workflow():

    workflow = create_default_assessment_workflow()

    assert isinstance(
        workflow,
        AssessmentWorkflow,
    )

    assert isinstance(
        workflow.analysis_agent,
        AnalysisAgent,
    )

    assert isinstance(
        workflow.reporting_agent,
        ReportingAgent,
    )

    assert isinstance(
        workflow.reporting_agent.report_generator,
        DeterministicReportGenerator,
    )


def test_workflow_factory_can_create_llm_workflow():

    workflow = create_default_assessment_workflow(
        use_llm=True,
    )

    assert isinstance(
        workflow,
        AssessmentWorkflow,
    )

    assert isinstance(
        workflow.analysis_agent,
        AnalysisAgent,
    )

    assert isinstance(
        workflow.reporting_agent,
        ReportingAgent,
    )

    assert isinstance(
        workflow.reporting_agent.report_generator,
        LLMReportGenerator,
    )

def test_llm_workflow_factory_creates_llm_reporting_agent():

    workflow = create_default_assessment_workflow(
        use_llm=True,
    )

    assert isinstance(
        workflow.reporting_agent,
        ReportingAgent,
    )

    assert isinstance(
        workflow.reporting_agent.report_generator,
        LLMReportGenerator,
    )