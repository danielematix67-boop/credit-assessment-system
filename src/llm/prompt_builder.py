from collections import defaultdict

from src.llm.prompt_template import ReportPromptTemplate
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis


class ReportPromptBuilder:
    """
    Builds prompts for LLM-based credit assessment reporting.

    The prompt builder prepares deterministic Analysis findings for the LLM
    using the authoritative assessment macro-area order.

    The deterministic assessment remains the sole source of truth.
    The LLM is responsible only for narrative generation.
    """

    _CATEGORY_PRIORITY = {
        "customer profile": 0,
        "financial analysis": 1,
        "behavioural analysis": 2,
        "debt sustainability": 3,
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

    @classmethod
    def _group_findings(
        cls,
        findings: list[AnalysisFinding],
    ) -> dict[str, list[AnalysisFinding]]:
        """Group deterministic findings by their authoritative assessment area."""
        grouped: dict[str, list[AnalysisFinding]] = defaultdict(list)

        for finding in findings:
            area = finding.assessment_area or finding.category
            grouped[area].append(finding)

        ordered_categories = sorted(
            grouped,
            key=lambda category: cls._CATEGORY_PRIORITY.get(
                category.casefold(),
                len(cls._CATEGORY_PRIORITY),
            ),
        )

        return {category: grouped[category] for category in ordered_categories}

    @staticmethod
    def _format_category_order(categories: list[str]) -> str:
        if not categories:
            return "None."

        return "\n".join(
            f"{index}. {category}"
            for index, category in enumerate(categories, start=1)
        )

    @staticmethod
    def _format_structured_value(value: object) -> str:
        """Format the deterministic structured value without changing its meaning."""
        if isinstance(value, str):
            return value
        return repr(value)

    @classmethod
    def _format_finding(cls, finding: AnalysisFinding) -> str:
        """Format one finding while preserving deterministic structured evidence."""
        lines = [f"- [{finding.severity.value.upper()}] {finding.text}"]

        if finding.indicator:
            lines.append(f"  Deterministic indicator: {finding.indicator}")

        if finding.value is not None:
            lines.append(
                "  Deterministic structured value: "
                f"{cls._format_structured_value(finding.value)}"
            )

        return "\n".join(lines)

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
                lines.append(cls._format_finding(finding))

            sections.append("\n".join(lines))

        return "\n\n".join(sections)
