from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.llm.client import LLMClient
from src.services.service_factory import create_default_assessment_service


def create_default_assessment_workflow(
    use_llm: bool = False,
    llm_client: LLMClient | None = None,
) -> AssessmentWorkflow:

    assessment_service = create_default_assessment_service()

    analysis_agent = AnalysisAgent()

    if use_llm:
        if llm_client is None:
            raise ValueError(
                "llm_client is required when use_llm=True"
            )

        report_generator = LLMReportGenerator(
            llm_client=llm_client,
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