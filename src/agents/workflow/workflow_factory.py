from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.services.service_factory import (
    create_default_assessment_service,
)


def create_default_assessment_workflow() -> AssessmentWorkflow:
    assessment_service = create_default_assessment_service()
    analysis_agent = AnalysisAgent()
    reporting_agent = ReportingAgent()

    return AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=analysis_agent,
        reporting_agent=reporting_agent,
    )