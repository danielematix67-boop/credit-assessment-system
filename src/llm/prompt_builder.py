from collections import defaultdict

from src.llm.prompt_template import ReportPromptTemplate
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.rules.base.status import RuleStatus


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

    _CATEGORY_PRIORITY_ORDER = (
        "Customer Profile",
        "Financial Analysis",
        "Behavioural Analysis",
        "Debt Sustainability",
    )

    # Narrative-ordering hints only: these never affect deterministic decisioning.
    _TOPIC_ORDER = {
        "revenue": (0, "Revenue and operating profitability"),
        "profitability": (0, "Revenue and operating profitability"),
        "profitability_quality": (1, "Earnings quality and operating structure"),
        "operating_leverage": (1, "Earnings quality and operating structure"),
        "working_capital": (2, "Working capital and cash conversion"),
        "leverage": (3, "Leverage and funding structure"),
        "asset_quality": (4, "Asset quality"),
        "utilization": (0, "Credit utilization and liquidity behaviour"),
        "overdraft": (0, "Credit utilization and liquidity behaviour"),
        "payment_behaviour": (1, "Payment behaviour"),
        "exposure": (2, "Exposure evolution"),
        "customer_profile": (0, "Customer profile risk signals"),
        "debt sustainability": (0, "Debt-service capacity"),
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
        if analysis.rule_evidence:
            # NOT_TRIGGERED rules are useful for audit/evidence views, but are
            # not adverse findings and overwhelm a compact executive narrative.
            findings = [
                finding
                for finding in analysis.rule_evidence
                if finding.status != RuleStatus.NOT_TRIGGERED
            ]
        else:
            findings = analysis.key_findings

        grouped_findings = self._group_findings(findings)

        # Always expose the complete assessment structure to the LLM so that
        # every executive report contains the same four macro-areas.
        grouped_findings = {
            area: grouped_findings.get(area, [])
            for area in self._CATEGORY_PRIORITY_ORDER
        }
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

        # Stable sort: findings in the same or an unknown topic keep source order.
        for area, area_findings in grouped.items():
            if area.casefold() in {
                "financial analysis",
                "behavioural analysis",
                "customer profile",
                "debt sustainability",
            }:
                area_findings.sort(
                    key=lambda finding: cls._topic_order(finding.category)[0]
                )

        ordered_categories = sorted(
            grouped,
            key=lambda category: cls._CATEGORY_PRIORITY.get(
                category.casefold(),
                len(cls._CATEGORY_PRIORITY),
            ),
        )

        return {category: grouped[category] for category in ordered_categories}

    @classmethod
    def _topic_order(cls, category: str) -> tuple[int, str]:
        """Return a stable narrative priority and theme for a rule category."""
        return cls._TOPIC_ORDER.get(
            category.strip().casefold(),
            (99, "Other findings"),
        )

    @staticmethod
    def _format_category_order(categories: list[str]) -> str:
        if not categories:
            return "None."

        return "\n".join(
            f"{index}. {category}"
            for index, category in enumerate(categories, start=1)
        )

    @staticmethod
    def _format_structured_value(value: object, finding: AnalysisFinding) -> str:
        """Format a deterministic value using the indicator's authoritative unit."""
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (int, float)):
            if "%" in finding.text:
                return f"{value:.1%}"
            if "€" in finding.text:
                return f"€{value:,.0f}"
            if "x" in finding.text.lower():
                return f"{value:.1f}x"
        if isinstance(value, str):
            return value
        return repr(value)

    @classmethod
    def _format_finding(cls, finding: AnalysisFinding) -> str:
        """Format one finding while preserving deterministic structured evidence."""
        if finding.status == RuleStatus.NOT_EVALUABLE:
            prefix = "NOT EVALUABLE"
        else:
            prefix = finding.severity.value.upper()
        lines = [f"- [{prefix}] {finding.text}"]

        if finding.indicator:
            lines.append(f"  Deterministic indicator: {finding.indicator}")
            lines.append("  Preserve this indicator label verbatim in the narrative.")

        if finding.value is not None:
            lines.append(
                "  Deterministic value: "
                f"{cls._format_structured_value(finding.value, finding)}"
            )

        return "\n".join(lines)

    @classmethod
    def _format_grouped_findings(
        cls,
        grouped_findings: dict[str, list[AnalysisFinding]],
    ) -> str:
        """
        Format deterministic rule findings for LLM narrative generation.

        Rule IDs and fixed contextual blocks are intentionally excluded:
        fixed Customer Profile and behavioural context are rendered by the
        application and added after narrative generation.
        """
        if not grouped_findings:
            return "None."

        sections: list[str] = []

        for category, findings in grouped_findings.items():
            lines = [f"{category}:"]

            if not findings:
                lines.append(
                    "  No deterministic anomalies are present for this area."
                )

            current_topic: str | None = None
            for finding in findings:
                _, topic = cls._topic_order(finding.category)
                if topic != current_topic:
                    lines.append(f"  Narrative theme: {topic}")
                    current_topic = topic
                lines.append(cls._format_finding(finding))

            sections.append("\n".join(lines))

        return "\n\n".join(sections)
