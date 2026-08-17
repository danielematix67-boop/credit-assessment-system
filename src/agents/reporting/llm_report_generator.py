import re

from src.agents.reporting.report_generator import ReportGenerator
from src.llm.client import LLMClient
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
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

        response = self._validate_response(
            response,
            analysis.assessment_status,
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

    @staticmethod
    def _validate_response(
        response: str,
        expected_status: AssessmentStatus,
    ) -> str:
        """
        Validate the integrity of the LLM response.

        The deterministic assessment status is the source of truth.

        The LLM must explicitly preserve the deterministic assessment
        status in the generated executive summary.

        Severity levels such as LOW, MEDIUM, or HIGH must not be
        confused with the assessment status.
        """

        # ========================================================
        # Debug information
        # ========================================================

        print("=" * 60)
        print("LLM REPORT VALIDATION")
        print(
            f"Expected assessment status: "
            f"{expected_status}"
        )
        print(
            f"Expected status value: "
            f"{expected_status.value}"
        )
        print(
            f"LLM response: "
            f"{repr(response)}"
        )
        print("=" * 60)

        # ========================================================
        # Empty response
        # ========================================================

        if not response or not response.strip():
            raise ValueError(
                "LLM returned an empty response"
            )

        normalized_response = response.strip().upper()

        # ========================================================
        # Detect assessment statuses
        # ========================================================

        status_values = [
            status.value
            for status in AssessmentStatus
        ]

        mentioned_statuses = [
            status
            for status in status_values
            if re.search(
                rf"\b{re.escape(status)}\b",
                normalized_response,
            )
        ]

        # ========================================================
        # Missing status
        # ========================================================

        if not mentioned_statuses:
            raise ValueError(
                "LLM response does not contain "
                "the assessment status"
            )

        # ========================================================
        # Wrong status
        # ========================================================

        if expected_status.value not in mentioned_statuses:
            raise ValueError(
                "LLM response does not contain "
                "the expected assessment status"
            )

        # ========================================================
        # Multiple statuses
        # ========================================================

        if len(set(mentioned_statuses)) > 1:
            raise ValueError(
                "LLM response contains multiple "
                "assessment statuses"
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
            "You must NOT reassess the credit position.\n"
            "You must NOT modify, override, or reinterpret the "
            "deterministic assessment.\n\n"

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
            "- Do not override or reinterpret the deterministic assessment.\n"
            "- Do not provide recommendations unless they are explicitly "
            "contained in the assessment.\n"
            "- Clearly distinguish between findings and limitations.\n"
            "- If information is missing or not evaluable, do not infer it.\n"
            "- Use concise and professional credit-risk language.\n"
            "- Do not disclose internal rule thresholds.\n"
            "- Do not reproduce threshold values.\n"
            "- Preserve the factual values when they are explicitly "
            "provided in the findings.\n\n"

            "IMPORTANT DISTINCTION:\n"
            "The assessment status and finding severity are different "
            "concepts.\n"
            "The assessment status is the overall deterministic outcome.\n"
            "Severity describes the severity of an individual finding.\n"
            "For example, MEDIUM is a severity level and must NOT be "
            "used as a replacement for the assessment status.\n\n"

            "ASSESSMENT INFORMATION:\n\n"

            f"Assessment status: "
            f"{analysis.assessment_status.value}\n\n"

            f"Key findings:\n"
            f"{analysis.key_findings}\n\n"

            f"Risk factors:\n"
            f"{analysis.risk_factors}\n\n"

            f"Limitations:\n"
            f"{analysis.limitations}\n\n"

            "MANDATORY STATUS REQUIREMENT:\n"
            f"The executive summary MUST explicitly contain the exact "
            f"assessment status '{analysis.assessment_status.value}'.\n"
            "You must reproduce the assessment status exactly as provided.\n"
            "Do not infer it.\n"
            "Do not calculate it.\n"
            "Do not replace it with a severity level.\n"
            "Do not omit it.\n\n"

            "REQUIRED OPENING:\n"
            f"The executive summary MUST begin with:\n"
            f"Assessment status: "
            f"{analysis.assessment_status.value}.\n\n"

            "TASK:\n"
            "Generate ONLY the executive summary.\n"
            "Start with the required assessment status sentence.\n"
            "Then provide a concise professional summary based "
            "exclusively on the provided assessment information.\n"
            "Do not add headings, metadata, analysis of your own, "
            "or information outside the assessment."
        )