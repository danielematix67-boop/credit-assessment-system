from src.agents.reporting.report_generator import ReportGenerator
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report, ReportFindingGroup


class DeterministicReportGenerator(ReportGenerator):

    def generate(
        self,
        analysis: AssessmentAnalysis,
    ) -> Report:

        if analysis.assessment_status == AssessmentStatus.NORMAL:
            summary = (
                "The credit assessment is classified as normal."
            )

        elif analysis.assessment_status == AssessmentStatus.ATTENTION:
            summary = (
                "The credit assessment requires attention."
            )

        elif analysis.assessment_status == AssessmentStatus.CRITICAL:
            summary = (
                "The credit assessment is classified as critical."
            )

        else:
            summary = (
                "The credit assessment has an undefined status."
            )

        findings_by_category = self._group_findings_by_category(
            analysis.key_findings
        )

        return Report(
            position_id=analysis.position_id,
            assessment_status=analysis.assessment_status,
            executive_summary=summary,
            findings_by_category=findings_by_category,
            limitations=analysis.limitations,
        )

    @staticmethod
    def _group_findings_by_category(
        findings,
    ) -> list[ReportFindingGroup]:

        grouped: dict[str, list] = {}

        for finding in findings:
            grouped.setdefault(finding.category, []).append(finding)

        return [
            ReportFindingGroup(
                category=category,
                findings=category_findings,
            )
            for category, category_findings in grouped.items()
        ]