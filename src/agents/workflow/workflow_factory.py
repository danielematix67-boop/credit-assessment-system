from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.llm.mock_client import MockLLMClient
from src.services.service_factory import create_default_assessment_service


def create_default_assessment_workflow(
    use_llm: bool = False,
) -> AssessmentWorkflow:

    assessment_service = create_default_assessment_service()

    analysis_agent = AnalysisAgent()

    if use_llm:
        report_generator = LLMReportGenerator(
            llm_client=MockLLMClient(),
        )
    else:
        report_generator = DeterministicReportGenerator()

    reporting_agent = ReportingAgent(
        report_generator=report_generator,
    )

    return AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=analysis_agent,
        reporting_agent=reporting_agent,
    )