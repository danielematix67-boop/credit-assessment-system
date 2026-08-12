from src.agents.analysis.analysis_agent import AnalysisAgent
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