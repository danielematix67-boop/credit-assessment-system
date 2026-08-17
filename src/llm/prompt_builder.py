from collections import defaultdict

from src.llm.prompt_template import ReportPromptTemplate
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis


class ReportPromptBuilder:
    """
    Builds prompts for LLM-based credit assessment reporting.

    The prompt builder prepares deterministic findings for the LLM
    by grouping them by financial category and ordering them by
    deterministic severity.

    The deterministic assessment remains the sole source of truth.
    The LLM is responsible only for narrative generation.
    """

    _SEVERITY_PRIORITY = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2,
    }

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

        Findings are grouped by category and ordered by deterministic
        severity before being passed to the LLM.

        Risk factors are not passed as a separate duplicated list,
        since they are already a subset of key findings.
        """

        grouped_findings = self._group_findings(
            analysis.key_findings,
        )

        return self.template.render(
            findings=self._format_grouped_findings(
                grouped_findings,
            ),
        )

    # ============================================================
    # Finding preparation
    # ============================================================

    @classmethod
    def _group_findings(
        cls,
        findings: list[AnalysisFinding],
    ) -> dict[str, list[AnalysisFinding]]:
        """
        Group findings by deterministic category.

        Findings within each category are ordered by severity.
        Original order is preserved for findings with equal severity.
        """

        grouped: dict[str, list[AnalysisFinding]] = defaultdict(list)

        for finding in findings:
            grouped[finding.category].append(finding)

        for category_findings in grouped.values():
            category_findings.sort(
                key=lambda finding: cls._SEVERITY_PRIORITY.get(
                    finding.severity.value.upper(),
                    99,
                )
            )

        return dict(grouped)

    # ============================================================
    # Formatting
    # ============================================================

    @classmethod
    def _format_grouped_findings(
        cls,
        grouped_findings: dict[str, list[AnalysisFinding]],
    ) -> str:
        """
        Format grouped deterministic findings for the LLM.

        Rule IDs are intentionally excluded from the narrative input
        because they are internal implementation details.
        """

        if not grouped_findings:
            return "None."

        sections: list[str] = []

        for category, findings in grouped_findings.items():
            lines = [f"{category}:"]

            for finding in findings:
                lines.append(
                    f"- [{finding.severity.value.upper()}] "
                    f"{finding.text}"
                )

            sections.append("\n".join(lines))

        return "\n\n".join(sections)