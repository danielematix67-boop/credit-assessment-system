from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.llm_report_generator import LLMReportGenerator
from src.agents.reporting.report_generator import ReportGenerator
from src.agents.reporting.reporting_agent import ReportingAgent
from src.agents.workflow.assessment_workflow import AssessmentWorkflow
from src.llm.client import LLMClient
from src.services.credit_assessment_case_service import CreditAssessmentCaseService
from src.services.service_factory import create_default_assessment_service


def create_default_assessment_workflow(
    use_llm: bool = False,
    llm_client: LLMClient | None = None,
) -> AssessmentWorkflow:
    assessment_service = create_default_assessment_service()
    credit_case_service = CreditAssessmentCaseService(assessment_service)
    case_analysis_agent = CaseAnalysisAgent()

    deterministic_report_generator = DeterministicReportGenerator()

    if use_llm:
        if llm_client is None:
            raise ValueError("llm_client is required when use_llm=True")
        report_generator: ReportGenerator = LLMReportGenerator(
            llm_client=llm_client,
        )
    else:
        report_generator = deterministic_report_generator

    reporting_agent = ReportingAgent(
        report_generator=report_generator,
        fallback_generator=deterministic_report_generator,
    )

    return AssessmentWorkflow(
        credit_case_service=credit_case_service,
        case_analysis_agent=case_analysis_agent,
        reporting_agent=reporting_agent,
    )
