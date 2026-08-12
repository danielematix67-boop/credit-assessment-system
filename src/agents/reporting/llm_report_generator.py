from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report


class LLMReportGenerator(ReportGenerator):

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:

        prompt = self._build_prompt(analysis)

        response = self.llm_client.generate(prompt)

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=response,
            findings=analysis.key_findings,
            limitations=analysis.limitations,
        )

    def _build_prompt(
        self,
        analysis: AssessmentAnalysis,
    ) -> str:

        return (
            "Generate a concise credit assessment summary.\n\n"
            f"Assessment status: {analysis.assessment_status.value}\n"
            f"Key findings: {analysis.key_findings}\n"
            f"Risk factors: {analysis.risk_factors}\n"
            f"Limitations: {analysis.limitations}\n\n"
            "The summary must be factual and must not introduce "
            "information that is not contained in the assessment."
        )