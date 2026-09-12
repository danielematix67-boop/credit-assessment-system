from collections import defaultdict

from src.llm.prompt_template import ReportPromptTemplate
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis


class ReportPromptBuilder:
    """
    Builds prompts for LLM-based credit assessment reporting.

    The prompt builder prepares deterministic findings for the LLM
    by grouping them by financial category and ordering them by
    deterministic category and severity.

    The deterministic assessment remains the sole source of truth.
    The LLM is responsible only for narrative generation.
    """

    _SEVERITY_PRIORITY = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2,
    }
    _CATEGORY_PRIORITY = {
        "revenue": 0,
        "profitability": 1,
        "leverage": 2,
    }

    def __init__(
        self,
        template: ReportPromptTemplate | None = None,
    ) -> None:
        self.template = template if template is not None else ReportPromptTemplate()

    def build(
        self,
        analysis: AssessmentAnalysis,
    ) -> str:
        """
        Build the complete prompt for executive narrative generation.

        Complete deterministic rule evidence is preferred when available;
        lightweight analyses without rule_evidence retain compatibility by
        falling back to key_findings.
        """
        findings = analysis.rule_evidence or analysis.key_findings
        grouped_findings = self._group_findings(findings)
        category_order = list(grouped_findings.keys())

        return self.template.render(
            findings=self._format_grouped_findings(grouped_findings),
            category_order=self._format_category_order(category_order),
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

        Categories follow the authoritative financial order: revenue,
        profitability, leverage, then any additional categories in first
        occurrence order. Findings within each category are ordered by
        severity, while equal-severity findings retain their source order.
        """

        grouped: dict[str, list[AnalysisFinding]] = defaultdict(list)

        for finding in findings:
            grouped[finding.category].append(finding)

        ordered_categories = sorted(
            grouped,
            key=lambda category: cls._CATEGORY_PRIORITY.get(
                category.casefold(),
                len(cls._CATEGORY_PRIORITY),
            ),
        )

        for category in ordered_categories:
            grouped[category].sort(
                key=lambda finding: cls._SEVERITY_PRIORITY.get(
                    finding.severity.value.upper(),
                    99,
                )
            )

        return {category: grouped[category] for category in ordered_categories}

    # ============================================================
    # Formatting
    # ============================================================

    @staticmethod
    def _format_category_order(categories: list[str]) -> str:
        if not categories:
            return "None."

        return "\n".join(
            f"{index}. {category}"
            for index, category in enumerate(categories, start=1)
        )

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
                lines.append(f"- [{finding.severity.value.upper()}] {finding.text}")

            sections.append("\n".join(lines))

        return "\n\n".join(sections)
