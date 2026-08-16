from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup


class LLMReportGenerator(ReportGenerator):
    """
    Report generator based on an abstract LLM client.

    The LLM is used exclusively to generate the executive summary.

    The deterministic assessment remains the source of truth for:
        - assessment status
        - rule findings
        - severity
        - limitations

    The implementation is provider-agnostic and can therefore be
    used with Gemini, Ollama, or any other LLMClient implementation.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:

        prompt = self._build_prompt(analysis)

        response = self.llm_client.generate(prompt)

        response = self._validate_response(response)

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

    @staticmethod
    def _validate_response(
        response: str,
    ) -> str:
        """
        Validate the basic integrity of the LLM response.

        The assessment status is intentionally NOT validated here.

        The status is already determined by the deterministic
        assessment engine and is stored independently in the Report.

        This prevents the reporting layer from failing simply because
        an LLM does not explicitly repeat the assessment status.
        """

        if not response or not response.strip():
            raise ValueError(
                "LLM returned an empty response"
            )

        return response.strip()

    @staticmethod
    def _build_prompt(
        analysis: AssessmentAnalysis,
    ) -> str:
        """
        Build the prompt used by the configured LLM provider.

        The prompt explicitly separates deterministic facts from
        the generative responsibility of the LLM.
        """

        return (
            "You are a credit assessment reporting assistant.\n\n"

            "The credit assessment has already been performed by a "
            "deterministic rule-based assessment engine.\n\n"

            "Your role is ONLY to transform the structured assessment "
            "results into a concise and professional executive summary.\n\n"

            "IMPORTANT ARCHITECTURAL CONSTRAINT:\n"
            "The deterministic assessment engine is the source of truth.\n"
            "You are NOT responsible for deciding the credit assessment.\n\n"

            "STRICT RULES:\n"
            "- Use EXCLUSIVELY the information provided below.\n"
            "- Do not introduce facts that are not present in the assessment.\n"
            "- Do not invent financial data.\n"
            "- Do not invent causes, explanations, or trends.\n"
            "- Do not reassess the credit position.\n"
            "- Do not reinterpret the rules.\n"
            "- Do not modify the assessment status.\n"
            "- Do not change the severity or meaning of any finding.\n"
            "- Do not make a credit decision.\n"
            "- Do not override the deterministic assessment.\n"
            "- Do not provide recommendations unless they are explicitly "
            "contained in the assessment.\n"
            "- Clearly distinguish findings from limitations.\n"
            "- If information is missing, do not infer it.\n"
            "- Use concise and professional credit-risk language.\n"
            "- Do not disclose internal rule thresholds.\n"
            "- Do not reproduce threshold values.\n"
            "- You may describe a metric as deteriorating, improving, "
            "above, below, or outside an acceptable level only when "
            "supported by the provided findings.\n"
            "- Preserve factual financial values when they are explicitly "
            "provided in the findings.\n\n"

            "ASSESSMENT INFORMATION:\n\n"

            f"Assessment status determined by the rule engine: "
            f"{analysis.assessment_status.value}\n\n"

            f"Key findings:\n"
            f"{analysis.key_findings}\n\n"

            f"Risk factors:\n"
            f"{analysis.risk_factors}\n\n"

            f"Limitations:\n"
            f"{analysis.limitations}\n\n"

            "TASK:\n"
            "Generate ONLY the executive summary.\n"
            "Do not add headings, metadata, analysis of your own, "
            "or information outside the assessment."
        )