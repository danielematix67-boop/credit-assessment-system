from app.config import (
    get_gemini_api_key,
    get_ollama_configuration,
)
from src.agents.analysis.case_analysis_agent import CaseAnalysisAgent
from src.agents.analysis.analysis_agent import AnalysisAgent
from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.llm_report_generator import (
    LLMReportGenerator,
)
from src.agents.reporting.reporting_agent import (
    ReportingAgent,
)
from src.agents.workflow.assessment_workflow import (
    AssessmentWorkflow,
)
from src.llm.gemini_client import GeminiClient
from src.llm.ollama_client import OllamaClient
from src.services.credit_assessment_case_service import CreditAssessmentCaseService
from src.services.service_factory import (
    create_default_assessment_service,
)


def create_workflow(
    reporting_mode: str,
    *,
    gemini_api_key: str | None = None,
    ollama_host: str | None = None,
    ollama_model: str | None = None,
) -> AssessmentWorkflow:
    assessment_service = create_default_assessment_service()
    credit_case_service = CreditAssessmentCaseService(assessment_service)
    analysis_agent = AnalysisAgent()
    case_analysis_agent = CaseAnalysisAgent()
    deterministic_report_generator = DeterministicReportGenerator()

    if reporting_mode == "Deterministic":
        reporting_agent = ReportingAgent(report_generator=deterministic_report_generator)
    elif reporting_mode == "Gemini + Fallback":
        if gemini_api_key is None:
            gemini_api_key = get_gemini_api_key()
        if not gemini_api_key:
            raise ValueError("Gemini API key is required for 'Gemini + Fallback' mode.")
        llm_client = GeminiClient(api_key=gemini_api_key)
        llm_report_generator = LLMReportGenerator(
            llm_client=llm_client,
            require_indicator_values=True,
        )
        reporting_agent = ReportingAgent(
            report_generator=llm_report_generator,
            fallback_generator=deterministic_report_generator,
        )
    elif reporting_mode == "Ollama + Fallback":
        if ollama_host is None or ollama_model is None:
            configured_host, configured_model = get_ollama_configuration()
            if ollama_host is None:
                ollama_host = configured_host
            if ollama_model is None:
                ollama_model = configured_model
        if not ollama_host:
            raise ValueError("Ollama host is required for 'Ollama + Fallback' mode.")
        if not ollama_model:
            raise ValueError("Ollama model is required for 'Ollama + Fallback' mode.")
        llm_client = OllamaClient(model=ollama_model, host=ollama_host)
        llm_report_generator = LLMReportGenerator(
            llm_client=llm_client,
            require_indicator_values=True,
        )
        reporting_agent = ReportingAgent(
            report_generator=llm_report_generator,
            fallback_generator=deterministic_report_generator,
        )
    else:
        raise ValueError(f"Unsupported reporting mode: {reporting_mode}")

    return AssessmentWorkflow(
        assessment_service=assessment_service,
        analysis_agent=analysis_agent,
        reporting_agent=reporting_agent,
        reporting_mode=reporting_mode,
        credit_case_service=credit_case_service,
        case_analysis_agent=case_analysis_agent,
    )
