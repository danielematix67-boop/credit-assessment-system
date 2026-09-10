from src.comments.comment import Comment
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.customer_profile_data import CustomerProfileData
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_status_calculator import AssessmentStatusCalculator


class CustomerProfileAssessmentService:
    """Build a deterministic customer profile and flag explicit credit-risk signals."""

    def __init__(self, status_calculator: AssessmentStatusCalculator | None = None):
        self.status_calculator = status_calculator or AssessmentStatusCalculator()

    def assess(self, data: CustomerProfileData) -> AssessmentSection:
        results = [
            self._boolean_flag("CP001", "Active EWS", data.active_ews),
            self._boolean_flag("CP002", "Previous Restructuring", data.previous_restructuring),
        ]
        evaluable_results = [
            result for result in results if result.status != RuleStatus.NOT_EVALUABLE
        ]
        has_profile_data = self._has_profile_data(data)
        if not has_profile_data:
            status = SectionStatus.NOT_EVALUABLE
        elif not evaluable_results:
            status = SectionStatus.NORMAL
        else:
            status = SectionStatus(self.status_calculator.calculate(evaluable_results).value)

        findings = [
            RuleFinding(result=result, comment=Comment(result.rule_id, result.reason or ""))
            for result in results
            if result.status == RuleStatus.TRIGGERED
        ]
        limitations = []
        if not has_profile_data:
            limitations.append("Customer profile data are not available.")
        elif not evaluable_results:
            limitations.append("No customer-profile risk flags could be evaluated.")

        return AssessmentSection(
            name="Customer Profile",
            status=status,
            findings=findings,
            evidence=results,
            limitations=limitations,
            context={
                "company_name": data.company_name,
                "legal_form": data.legal_form,
                "sector": data.sector,
                "size_class": data.size_class,
                "geography": data.geography,
                "shareholders": list(data.shareholders),
                "management_members": list(data.management_members),
                "relationship_years": data.relationship_years,
                "historical_facilities": list(data.historical_facilities),
            },
        )

    @staticmethod
    def _has_profile_data(data: CustomerProfileData) -> bool:
        return any(
            value not in (None, "", [])
            for value in (
                data.company_name,
                data.legal_form,
                data.sector,
                data.size_class,
                data.geography,
                data.shareholders,
                data.management_members,
                data.relationship_years,
                data.historical_facilities,
                data.active_ews,
                data.previous_restructuring,
            )
        )

    @staticmethod
    def _boolean_flag(rule_id: str, rule_name: str, value: bool | None) -> RuleResult:
        if value is None:
            return RuleResult(
                rule_id=rule_id,
                rule_name=rule_name,
                category="Customer Profile",
                status=RuleStatus.NOT_EVALUABLE,
                value=None,
                threshold=1.0,
                severity=RuleSeverity.MEDIUM,
                reason=f"[{rule_id} - {rule_name}] {rule_name} is not available.",
                indicator=rule_name,
                direction=SeverityDirection.HIGHER_IS_WORSE,
            )

        status = RuleStatus.TRIGGERED if value else RuleStatus.NOT_TRIGGERED
        return RuleResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category="Customer Profile",
            status=status,
            value=1.0 if value else 0.0,
            threshold=1.0,
            severity=RuleSeverity.HIGH if value else RuleSeverity.MEDIUM,
            reason=(
                f"[{rule_id} - {rule_name}] {rule_name} is present."
                if value
                else f"[{rule_id} - {rule_name}] {rule_name} is not present."
            ),
            indicator=rule_name,
            direction=SeverityDirection.HIGHER_IS_WORSE,
        )
