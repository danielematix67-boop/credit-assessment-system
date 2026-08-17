from src.llm.prompt_template import ReportPromptTemplate
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis


class ReportPromptBuilder:
    """
    Builds prompts for LLM-based credit assessment reporting.

    The prompt builder is responsible only for:

    - extracting deterministic assessment data;
    - serializing findings and limitations;
    - passing the structured data to the prompt template.

    It does not perform assessment logic and does not modify
    deterministic findings, severities, categories, or status.

    Prompt wording and instructions are delegated entirely to
    ReportPromptTemplate.
    """

    def __init__(
        self,
        template: ReportPromptTemplate | None = None,
    ) -> None:
        self.template = (
            template
            if template is not None
            else ReportPromptTemplate()
        )

    def build(
        self,
        analysis: AssessmentAnalysis,
    ) -> str:
        """
        Build the complete prompt for executive narrative generation.

        The deterministic assessment remains the source of truth.
        """

        return self.template.render(
            assessment_status=analysis.assessment_status.value,
            key_findings=self._format_findings(
                analysis.key_findings,
            ),
            risk_factors=self._format_findings(
                analysis.risk_factors,
            ),
            limitations=self._format_limitations(
                analysis.limitations,
            ),
        )

    # ============================================================
    # Finding formatting
    # ============================================================

    @staticmethod
    def _format_finding(
        finding: AnalysisFinding,
    ) -> str:
        """
        Serialize one deterministic finding.

        All semantic metadata required by the LLM is preserved.
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
        Serialize a collection of deterministic findings.

        The implementation is independent of the number,
        categories, rule IDs, and severity values.
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

        Limitations retain their semantic metadata but remain
        explicitly distinguishable from findings through the
        prompt template.
        """

        if not limitations:
            return "None."

        return "\n".join(
            cls._format_finding(limitation)
            for limitation in limitations
        )