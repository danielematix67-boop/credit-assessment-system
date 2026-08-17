from src.llm.prompt_template import ReportPromptTemplate
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis


class ReportPromptBuilder:
    """
    Builds prompts for LLM-based credit assessment reporting.

    The prompt builder extracts only the deterministic findings
    required for executive narrative generation.

    Assessment status and limitations are deliberately excluded
    from the LLM prompt and remain deterministic report data.
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
        """

        return self.template.render(
            key_findings=self._format_findings(
                analysis.key_findings,
            ),
            risk_factors=self._format_findings(
                analysis.risk_factors,
            ),
        )

    @staticmethod
    def _format_finding(
        finding: AnalysisFinding,
    ) -> str:
        """
        Serialize one deterministic finding.
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
        """

        if not findings:
            return "None."

        return "\n".join(
            cls._format_finding(finding)
            for finding in findings
        )