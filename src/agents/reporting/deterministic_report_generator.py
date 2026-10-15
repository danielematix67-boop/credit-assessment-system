from src.agents.reporting.report_generator import ReportGenerator
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup
from src.rules.base.status import RuleStatus


class DeterministicReportGenerator(ReportGenerator):
    _ASSESSMENT_AREA_ORDER = (
        "Customer Profile",
        "Financial Analysis",
        "Behavioural Analysis",
        "Debt Sustainability",
    )

    # Presentation priorities aligned with the LLM prompt builder.
    _TOPIC_ORDER = {
        "revenue": 0,
        "profitability": 0,
        "profitability_quality": 1,
        "operating_leverage": 1,
        "working_capital": 2,
        "leverage": 3,
        "asset_quality": 4,
        "utilization": 0,
        "overdraft": 0,
        "payment_behaviour": 1,
        "payment_behavior": 1,
        "exposure": 2,
        "customer_profile": 0,
        "debt_sustainability": 0,
    }

    _NO_ANOMALY_TEXT = (
        "No anomalies were identified by the configured deterministic "
        "assessment rules in this area."
    )

    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:
        self._validate_rule_evidence(analysis.key_findings)
        summary = self._generate_summary(analysis)
        findings_by_category = self._group_findings_by_category(analysis.key_findings)

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=summary,
            findings_by_category=findings_by_category,
            limitations=analysis.limitations,
        )

    @classmethod
    def _generate_summary(
        cls,
        analysis: AssessmentAnalysis,
    ) -> str:
        """Build the fallback narrative using all authoritative assessment areas."""
        status = f"Assessment Status: {analysis.assessment_status.value.capitalize()}"

        evidence = analysis.rule_evidence or analysis.key_findings
        grouped: dict[str, list[AnalysisFinding]] = {}
        for finding in evidence:
            area = finding.assessment_area or finding.category
            grouped.setdefault(area, []).append(finding)

        profile_text = ""
        if analysis.customer_profile is not None:
            profile_text = cls._render_customer_profile_context(
                analysis.customer_profile.sections()
            )

        paragraphs: list[tuple[str, str]] = []
        canonical = {area.casefold() for area in cls._ASSESSMENT_AREA_ORDER}

        for area in cls._ASSESSMENT_AREA_ORDER:
            area_findings = [
                finding
                for category, items in grouped.items()
                if category.casefold() == area.casefold()
                for finding in items
            ]
            triggered = sorted(
                (finding for finding in area_findings if cls._is_triggered(finding)),
                key=lambda finding: cls._topic_order(finding.category),
            )

            if area.casefold() == "customer profile" and profile_text:
                # Keep the complete contextual profile and append triggered
                # deterministic evidence, because rule-backed fields are
                # intentionally excluded from the material context subset.
                paragraph = profile_text
                if triggered:
                    context_key = cls._normalize_text(profile_text)
                    distinct_rule_sentences = [
                        finding.text.rstrip(".") + "."
                        for finding in triggered
                        if finding.indicator
                        and cls._normalize_text(finding.indicator) not in context_key
                    ]
                    if distinct_rule_sentences:
                        paragraph += (
                            "\n\n**Deterministic rule findings**\n\n"
                            + " ".join(distinct_rule_sentences)
                        )
            else:
                sentences = [
                    finding.text.rstrip(".") + "."
                    for finding in triggered
                ]
                paragraph = " ".join(sentences).strip()
            if not paragraph:
                paragraph = cls._NO_ANOMALY_TEXT

            paragraphs.append((area, paragraph))

        for category, findings in grouped.items():
            if category.casefold() in canonical:
                continue
            triggered = sorted(
                (finding for finding in findings if cls._is_triggered(finding)),
                key=lambda finding: cls._topic_order(finding.category),
            )
            if triggered:
                paragraphs.append(
                    (
                        category,
                        " ".join(
                            finding.text.rstrip(".") + "."
                            for finding in triggered
                        ),
                    )
                )

        narrative_parts: list[str] = []
        for category, paragraph in paragraphs:
            if category.casefold() in canonical:
                narrative_parts.append(f"### {category}\n\n{paragraph}")
            else:
                narrative_parts.append(paragraph)

        return f"{status}\n\n{'\n\n'.join(narrative_parts)}"

    @staticmethod
    def _render_customer_profile_context(
        sections: list[tuple[str, str]],
    ) -> str:
        """Render profile context as compact prose without nested subsection headings."""
        import re

        paragraphs: list[str] = []
        for _, content in sections:
            if not content:
                continue
            # Keep structured sections internally, but omit their headings from
            # the deterministic executive narrative to avoid excessive nesting.
            cleaned = re.sub(r"(?m)^\*\*[^\n]+\*\*\s*", "", content).strip()
            cleaned = re.sub(r"\s+", " ", cleaned)
            if cleaned and cleaned != "No additional information available.":
                paragraphs.append(cleaned)
        return " ".join(paragraphs)

    @classmethod
    def _ordered_categories(
        cls,
        grouped: dict[str, list[AnalysisFinding]],
    ) -> list[str]:
        """Return assessment areas in their authoritative order."""
        canonical = {area.casefold(): area for area in cls._ASSESSMENT_AREA_ORDER}
        ordered: list[str] = []

        for area in cls._ASSESSMENT_AREA_ORDER:
            if area.casefold() in {item.casefold() for item in grouped}:
                ordered.append(area)

        ordered.extend(
            category
            for category in grouped
            if category.casefold() not in canonical
        )
        return ordered

    @staticmethod
    def _validate_rule_evidence(findings: list[AnalysisFinding]) -> None:
        """Reject rule evidence that is not backed by a structured deterministic status."""
        missing_status = [
            finding.rule_id
            for finding in findings
            if finding.status is None
        ]
        if missing_status:
            rule_ids = ", ".join(missing_status)
            raise ValueError(
                "Rule evidence requires a structured RuleStatus; "
                f"missing status for: {rule_ids}"
            )

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize text for conservative duplicate checks in the fallback."""
        import re

        return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

    @classmethod
    def _topic_order(cls, category: str) -> int:
        """Return a narrative priority for a configured rule category."""
        normalized = category.strip().casefold().replace(" ", "_")
        return cls._TOPIC_ORDER.get(normalized, 99)

    @staticmethod
    def _is_triggered(finding: AnalysisFinding) -> bool:
        """Return whether structured deterministic evidence is triggered."""
        return finding.status == RuleStatus.TRIGGERED

    @staticmethod
    def _group_findings_by_category(
        findings: list[AnalysisFinding],
    ) -> list[ReportFindingGroup]:
        """Group deterministic findings by their original category."""
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
