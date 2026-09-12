from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.final_assessment import FinalAssessment
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class CaseAnalysisAgent:
    """Adapt deterministic case evidence into the reporting analysis contract."""

    def run(self, case: CreditAssessmentCase) -> AssessmentAnalysis:
        final_assessment = case.final_assessment or self._require_final_assessment(case)
        rule_evidence: list[AnalysisFinding] = []
        risk_factors: list[AnalysisFinding] = []
        limitations: list[AnalysisFinding] = []

        if case.customer_profile.context:
            summary = self._profile_summary(case.customer_profile.context)
            if summary:
                rule_evidence.append(
                    AnalysisFinding(
                        rule_id="PROFILE",
                        category="Customer Profile",
                        severity=RuleSeverity.MEDIUM,
                        text=summary,
                    )
                )

        for section in case.sections:
            triggered_text_by_rule = {
                finding.result.rule_id: finding.comment.text
                for finding in section.findings
            }
            section_rule_evidence = [
                self._rule_evidence_finding(
                    result,
                    triggered_text=triggered_text_by_rule.get(result.rule_id),
                )
                for result in section.evidence
            ]

            # Keep compatibility with lightweight unit-test sections that may
            # provide findings without duplicating the deterministic evidence.
            if not section_rule_evidence:
                section_rule_evidence = [
                    AnalysisFinding(
                        rule_id=finding.result.rule_id,
                        category=finding.result.category,
                        severity=finding.result.severity,
                        text=finding.comment.text,
                    )
                    for finding in section.findings
                ]

            rule_evidence.extend(section_rule_evidence)

            for finding in section.findings:
                if (
                    finding.result.status == RuleStatus.TRIGGERED
                    and finding.result.severity == RuleSeverity.HIGH
                ):
                    risk_factors.append(
                        next(
                            evidence
                            for evidence in section_rule_evidence
                            if evidence.rule_id == finding.result.rule_id
                        )
                    )

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
            # key_findings is the reporting input and contains all deterministic
            # rule results, not only triggered rules.
            key_findings=rule_evidence,
            risk_factors=risk_factors,
            limitations=limitations,
            rule_evidence=rule_evidence,
        )

    @staticmethod
    def _rule_evidence_finding(
        result: RuleResult,
        *,
        triggered_text: str | None = None,
    ) -> AnalysisFinding:
        """Expose every deterministic rule result without exposing thresholds."""
        if result.status == RuleStatus.TRIGGERED:
            text = triggered_text or result.indicator
        elif result.status == RuleStatus.NOT_TRIGGERED:
            value = CaseAnalysisAgent._format_value(result.value)
            text = f"{result.indicator} is {value} and does not trigger a risk condition."
        else:
            text = f"{result.indicator} is not available and cannot be evaluated."

        return AnalysisFinding(
            rule_id=result.rule_id,
            category=result.category,
            severity=result.severity,
            text=text,
        )

    @staticmethod
    def _format_value(value: object) -> str:
        if isinstance(value, float):
            return f"{value:g}"
        return str(value)

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
