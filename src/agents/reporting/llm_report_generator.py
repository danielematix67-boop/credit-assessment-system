from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup


class LLMReportGenerator(ReportGenerator):

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:

        prompt = self._build_prompt(analysis)

        response = self.llm_client.generate(prompt)

        response = self._validate_response(
            response,
            analysis,
        )

        findings_by_category = self._group_findings_by_category(
            analysis.key_findings
        )

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=response,
            findings_by_category=findings_by_category,
            limitations=analysis.limitations,
        )

    @staticmethod
    def _group_findings_by_category(
        findings: list[AnalysisFinding],
    ) -> list[ReportFindingGroup]:

        grouped: dict[str, list[AnalysisFinding]] = {}

        for finding in findings:
            grouped.setdefault(
                finding.category,
                [],
            ).append(finding)

        return [
            ReportFindingGroup(
                category=category,
                findings=category_findings,
            )
            for category, category_findings in grouped.items()
        ]

    def _validate_response(
        self,
        response: str,
        analysis: AssessmentAnalysis,
    ) -> str:

        if not response.strip():
            raise ValueError(
                "LLM returned an empty response"
            )

        status = analysis.assessment_status.value

        if status not in response.upper():
            raise ValueError(
                "LLM response does not contain "
                "the assessment status"
            )

        return response

    def _build_prompt(
        self,
        analysis: AssessmentAnalysis,
    ) -> str:

        return (
            "You are a credit assessment reporting assistant.\n\n"

            "The credit assessment has already been performed by a "
            "deterministic rule-based assessment engine. "
            "Your role is ONLY to transform the structured assessment "
            "results into a concise, professional executive summary.\n\n"

            "You must NOT reassess the credit position, reinterpret the "
            "rules, or make independent decisions.\n\n"

            "STRICT RULES:\n"
            "- Use EXCLUSIVELY the information provided in the assessment.\n"
            "- Do not introduce facts that are not present in the assessment.\n"
            "- Do not invent financial data, causes, explanations, or trends.\n"
            "- Do not modify the assessment status.\n"
            "- Do not change the severity or meaning of any finding.\n"
            "- Do not make a credit decision.\n"
            "- Do not override or reinterpret the deterministic assessment.\n"
            "- Do not provide recommendations unless they are explicitly "
            "contained in the assessment.\n"
            "- Clearly distinguish between findings and limitations.\n"
            "- If information is missing or not evaluable, do not infer it.\n"
            "- Use professional and concise credit-risk language.\n"
            "- Do not disclose internal rule thresholds in the executive summary.\n"
            "- Do not reproduce threshold values from the assessment.\n"
            "- You may describe a metric as above, below, or outside an "
            "acceptable level when this is supported by the findings.\n"
            "- Preserve the factual values of financial metrics when they "
            "are explicitly provided in the findings.\n"
            "- The assessment status must remain exactly as provided.\n\n"

            "ASSESSMENT:\n"
            f"Assessment status: "
            f"{analysis.assessment_status.value}\n"
            f"Key findings: {analysis.key_findings}\n"
            f"Risk factors: {analysis.risk_factors}\n"
            f"Limitations: {analysis.limitations}\n\n"

            "Generate ONLY the executive summary."
        )
