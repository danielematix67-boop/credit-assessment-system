from src.agents.reporting.report_generator import ReportGenerator
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report, ReportFindingGroup


class DeterministicReportGenerator(ReportGenerator):
    _STATUS_DESCRIPTIONS = {
        AssessmentStatus.NORMAL: "No significant credit-risk factors identified",
        AssessmentStatus.ATTENTION: "Credit-risk factors requiring monitoring identified",
        AssessmentStatus.CRITICAL: (
            "Significant credit-risk factors affecting the credit profile identified"
        ),
    }

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

    @classmethod
    def _generate_summary(
        cls,
        analysis: AssessmentAnalysis,
    ) -> str:
        status = analysis.assessment_status
        description = cls._STATUS_DESCRIPTIONS.get(
            status,
            "Assessment status could not be determined",
        )
        status_value = getattr(status, "value", str(status))

        summary = (
            f"Assessment status: {status_value} — {description}.\n"
            "The credit assessment identifies the following relevant findings."
        )

        if analysis.risk_factors:
            summary += "\n"
            summary += " ".join(
                risk_factor.text.rstrip(".") + "."
                for risk_factor in analysis.risk_factors
            )

        elif analysis.key_findings:
            summary += "\n"
            summary += " ".join(
                finding.text.rstrip(".") + "."
                for finding in analysis.key_findings
            )

        return summary

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
