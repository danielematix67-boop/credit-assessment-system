from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.final_assessment import FinalAssessment
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus


class CaseAnalysisAgent:
    """Adapt deterministic case evidence into the existing analysis contract."""

    def run(self, case: CreditAssessmentCase) -> AssessmentAnalysis:
        final_assessment = case.final_assessment or self._require_final_assessment(case)
        findings: list[AnalysisFinding] = []
        risk_factors: list[AnalysisFinding] = []
        limitations: list[AnalysisFinding] = []

        if case.customer_profile.context:
            summary = self._profile_summary(case.customer_profile.context)
            if summary:
                findings.append(
                    AnalysisFinding(
                        rule_id="PROFILE",
                        category="Customer Profile",
                        severity=RuleSeverity.MEDIUM,
                        text=summary,
                    )
                )

        for section in case.sections:
            for finding in section.findings:
                analysis_finding = AnalysisFinding(
                    rule_id=finding.result.rule_id,
                    category=finding.result.category,
                    severity=finding.result.severity,
                    text=finding.comment.text,
                )
                findings.append(analysis_finding)
                if finding.result.status == RuleStatus.TRIGGERED and finding.result.severity == RuleSeverity.HIGH:
                    risk_factors.append(analysis_finding)

            for limitation in section.limitations:
                limitations.append(
                    AnalysisFinding(
                        rule_id=f"SECTION:{section.name}",
                        category=section.name,
                        severity=RuleSeverity.MEDIUM,
                        text=limitation,
                    )
                )

        for limitation in final_assessment.limitations:
            limitations.append(
                AnalysisFinding(
                    rule_id="FINAL",
                    category="Final Assessment",
                    severity=RuleSeverity.MEDIUM,
                    text=limitation,
                )
            )

        return AssessmentAnalysis(
            position_id=case.position.position_id,
            assessment_status=self._to_assessment_status(final_assessment),
            key_findings=findings,
            risk_factors=risk_factors,
            limitations=limitations,
        )

    @staticmethod
    def _require_final_assessment(case: CreditAssessmentCase) -> FinalAssessment:
        from src.services.final_assessment_service import FinalAssessmentService

        return FinalAssessmentService().assess(case)

    @staticmethod
    def _to_assessment_status(final_assessment: FinalAssessment) -> AssessmentStatus:
        return AssessmentStatus(final_assessment.status.value)

    @staticmethod
    def _profile_summary(profile: dict[str, object]) -> str:
        fields = (
            ("Company", profile.get("company_name")),
            ("Legal form", profile.get("legal_form")),
            ("Sector", profile.get("sector")),
            ("Size class", profile.get("size_class")),
            ("Geography", profile.get("geography")),
            ("Relationship years", profile.get("relationship_years")),
        )
        return "; ".join(f"{label}: {value}" for label, value in fields if value not in (None, ""))
