from src.agents.reporting.report_generator import ReportGenerator
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.report import Report, ReportFindingGroup


class DeterministicReportGenerator(ReportGenerator):
    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:
        summary = self._generate_summary(analysis)
        findings_by_category = self._group_findings_by_category(analysis.key_findings)

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=summary,
            findings_by_category=findings_by_category,
            limitations=analysis.limitations,
        )

    @staticmethod
    def _generate_summary(
        analysis: AssessmentAnalysis,
    ) -> str:
        """Build a complete, category-ordered fallback narrative."""
        status_value = getattr(
            analysis.assessment_status,
            "value",
            str(analysis.assessment_status),
        )
        status_label = str(status_value).capitalize()
        summary = f"Assessment Status: {status_label}"

        findings = analysis.key_findings
        if not findings:
            return summary

        grouped: dict[str, list[AnalysisFinding]] = {}
        for finding in findings:
            grouped.setdefault(finding.category, []).append(finding)

        paragraphs = [
            " ".join(finding.text.rstrip(".") + "." for finding in category_findings)
            for category_findings in grouped.values()
        ]
        return summary + "\n\n" + "\n\n".join(paragraphs)

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
