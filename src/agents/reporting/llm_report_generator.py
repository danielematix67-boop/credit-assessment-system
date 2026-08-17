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

    The LLM is used exclusively to generate the executive narrative.

    The deterministic assessment remains the source of truth for:
        - assessment status
        - rule findings
        - finding severity
        - finding categories
        - limitations

    The LLM does NOT generate or determine the assessment status.

    The implementation is provider-agnostic and can therefore be
    used with Gemini, Ollama, or any other LLMClient implementation.
    """

    def __init__(
        self,
        llm_client: LLMClient,
    ) -> None:
        self.llm_client = llm_client

    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:
        """
        Generate a report using the configured LLM.

        The LLM generates only the executive narrative.

        The assessment status is always taken from the deterministic
        assessment and is added by this generator.

        All structured assessment information is preserved from
        the deterministic assessment.
        """

        prompt = self._build_prompt(analysis)

        response = self.llm_client.generate(prompt)

        validated_response = self._validate_response(response)

        executive_summary = (
            f"Assessment status: "
            f"{analysis.assessment_status.value}.\n"
            f"{validated_response}"
        )

        findings_by_category = (
            self._group_findings_by_category(
                analysis.key_findings,
            )
        )

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=executive_summary,
            findings_by_category=findings_by_category,
            limitations=analysis.limitations,
        )

    # ============================================================
    # Finding grouping
    # ============================================================

    @staticmethod
    def _group_findings_by_category(
        findings: list[AnalysisFinding],
    ) -> list[ReportFindingGroup]:
        """
        Group deterministic findings by category.

        The grouping is deterministic and completely independent
        of the LLM output.

        The original finding order is preserved.
        """

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

    # ============================================================
    # Prompt formatting
    # ============================================================

    @staticmethod
    def _format_finding(
        finding: AnalysisFinding,
    ) -> str:
        """
        Serialize one deterministic finding for the LLM.

        The complete semantic metadata is explicitly represented.

        No information is inferred or generated here.
        """

        return (
            f"- Rule ID: {finding.rule_id}\n"
            f"  Category: {finding.category}\n"
            f"  Severity: {finding.severity.value}\n"
            f"  Finding: {finding.text}"
        )

    @classmethod
    def _format_findings(
        cls,
        findings: list[AnalysisFinding],
    ) -> str:
        """
        Serialize a dynamic collection of findings.

        The implementation is intentionally independent of the
        number, IDs, categories, or severity values of findings.
        """

        if not findings:
            return "None."

        return "\n".join(
            cls._format_finding(finding)
            for finding in findings
        )

    @classmethod
    def _format_limitations(
        cls,
        limitations: list[AnalysisFinding],
    ) -> str:
        """
        Serialize deterministic limitations.

        Limitations retain their metadata so that the LLM has
        complete contextual information, while the instructions
        explicitly prevent them from becoming new findings.
        """

        if not limitations:
            return "None."

        return "\n".join(
            cls._format_finding(limitation)
            for limitation in limitations
        )

    # ============================================================
    # Response validation
    # ============================================================

    @staticmethod
    def _validate_response(
        response: str,
    ) -> str:
        """
        Validate the LLM-generated narrative.

        The LLM is responsible only for language generation.

        The deterministic assessment status is NOT expected in the
        LLM response and is deliberately excluded from validation.

        Validation rules:

        1. The response must not be empty.
        2. Whitespace-only responses are rejected.
        3. The original response content is preserved.
        """

        if not response or not response.strip():
            raise ValueError(
                "LLM returned an empty response"
            )

        return response.strip()

    # ============================================================
    # Prompt construction
    # ============================================================

    @classmethod
    def _build_prompt(
        cls,
        analysis: AssessmentAnalysis,
    ) -> str:
        """
        Build the prompt used by the configured LLM provider.

        The prompt explicitly separates:

            deterministic assessment
                    |
                    +-- assessment status
                    +-- findings
                    +-- risk factors
                    +-- limitations
                    |
                    v
                  LLM
                    |
                    +-- executive narrative only

        The LLM is never responsible for generating the assessment
        status or other structured assessment information.

        All assessment content is generated dynamically from the
        AssessmentAnalysis object.
        """

        key_findings = cls._format_findings(
            analysis.key_findings,
        )

        risk_factors = cls._format_findings(
            analysis.risk_factors,
        )

        limitations = cls._format_limitations(
            analysis.limitations,
        )

        return (
            # ----------------------------------------------------
            # ROLE
            # ----------------------------------------------------

            "You are a credit assessment reporting assistant.\n\n"

            "Your role is to transform the provided deterministic "
            "credit assessment information into a concise and "
            "professional executive narrative.\n\n"

            "The credit assessment has already been performed by a "
            "deterministic rule-based assessment engine.\n\n"

            "The deterministic assessment engine is the source of "
            "truth. You are responsible ONLY for language generation "
            "and summarisation.\n\n"

            # ----------------------------------------------------
            # STATUS BOUNDARY
            # ----------------------------------------------------

            "ASSESSMENT STATUS BOUNDARY:\n"
            "The assessment status is owned exclusively by the "
            "deterministic assessment engine.\n"
            "Do NOT generate an assessment status.\n"
            "Do NOT classify the assessment as NORMAL, ATTENTION, "
            "CRITICAL, or any other status.\n"
            "Do NOT infer an overall assessment status from the "
            "findings.\n"
            "Do NOT replace, reinterpret, or modify the deterministic "
            "assessment outcome.\n"
            "The application will add the deterministic assessment "
            "status to the final report.\n\n"

            # ----------------------------------------------------
            # ARCHITECTURAL BOUNDARY
            # ----------------------------------------------------

            "ROLE BOUNDARY:\n"
            "- The deterministic engine performs the assessment.\n"
            "- The analysis object contains the deterministic "
            "assessment.\n"
            "- You are responsible ONLY for language generation "
            "and summarisation.\n"
            "- Do not reassess the credit position.\n"
            "- Do not override the deterministic assessment.\n"
            "- Do not make a credit decision.\n"
            "- Do not modify any structured assessment information.\n\n"

            # ----------------------------------------------------
            # SAFETY CONSTRAINTS
            # ----------------------------------------------------

            "SAFETY CONSTRAINTS:\n"
            "- Use exclusively the information provided below.\n"
            "- Do not introduce facts that are not present in the "
            "provided information.\n"
            "- Do not invent financial data.\n"
            "- Do not invent causes, events, trends, or explanations.\n"
            "- Do not reassess any rule result.\n"
            "- Do not modify the assessment status.\n"
            "- Do not modify finding severity.\n"
            "- Do not modify finding categories.\n"
            "- Do not create new findings.\n"
            "- Do not remove deterministic findings.\n"
            "- Do not change the meaning of a finding.\n"
            "- Do not make a credit decision.\n"
            "- Do not provide recommendations.\n"
            "- Do not disclose internal rule thresholds.\n"
            "- Do not reproduce threshold values.\n"
            "- Preserve factual values exactly when they are included "
            "in the source findings.\n\n"

            # ----------------------------------------------------
            # SEMANTIC DISTINCTION
            # ----------------------------------------------------

            "IMPORTANT SEMANTIC DISTINCTION:\n"
            "Assessment status represents the overall deterministic "
            "assessment outcome and is NOT generated by you.\n"
            "Severity represents the severity of an individual finding.\n"
            "Category identifies the financial or risk area associated "
            "with a finding.\n"
            "Rule ID identifies the deterministic rule that produced "
            "the finding.\n"
            "These concepts must not be confused or modified.\n\n"

            # ----------------------------------------------------
            # DETERMINISTIC INPUT
            # ----------------------------------------------------

            "DETERMINISTIC ASSESSMENT INPUT:\n\n"

            "Assessment status:\n"
            f"{analysis.assessment_status.value}\n\n"

            "Key findings:\n"
            f"{key_findings}\n\n"

            "Risk factors:\n"
            f"{risk_factors}\n\n"

            "Limitations:\n"
            f"{limitations}\n\n"

            # ----------------------------------------------------
            # LIMITATIONS
            # ----------------------------------------------------

            "LIMITATION HANDLING:\n"
            "- A limitation represents information that could not "
            "be evaluated.\n"
            "- Do not treat a limitation as a finding.\n"
            "- Do not infer the missing value.\n"
            "- Do not transform a limitation into a risk conclusion.\n"
            "- Do not invent information to compensate for a limitation.\n\n"

            # ----------------------------------------------------
            # NARRATIVE
            # ----------------------------------------------------

            "NARRATIVE GUIDANCE:\n"
            "- Produce a concise professional credit-risk narrative.\n"
            "- Preserve the meaning of the supplied findings.\n"
            "- Prioritise material findings when appropriate.\n"
            "- Group related information naturally when supported "
            "by the supplied categories.\n"
            "- Do not infer causality unless it is explicitly supported.\n"
            "- Do not infer trends that are not present in the findings.\n"
            "- Do not use temporal expressions unless supported by "
            "the supplied information.\n"
            "- Do not describe values as exceeding an acceptable level "
            "unless explicitly stated in the supplied information.\n"
            "- Avoid simply reproducing the complete finding list.\n"
            "- Do not introduce information that is absent from the "
            "deterministic assessment.\n\n"

            # ----------------------------------------------------
            # OUTPUT CONTRACT
            # ----------------------------------------------------

            "OUTPUT REQUIREMENTS:\n"
            "- Generate ONLY the executive narrative.\n"
            "- Do NOT generate the assessment status.\n"
            "- Do NOT start with 'Assessment status:'.\n"
            "- Do not add headings.\n"
            "- Do not add bullet points.\n"
            "- Do not add metadata.\n"
            "- Do not add recommendations.\n"
            "- Do not mention internal rules or thresholds.\n"
            "- Do not mention that an LLM was used.\n"
        )