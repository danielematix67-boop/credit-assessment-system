from src.comments.comment import Comment
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.behavioural_data import BehaviouralData
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_status_calculator import AssessmentStatusCalculator


class BehaviouralAssessmentService:
    """Deterministically assess banking-behaviour indicators."""

    _RULES = (
        ("B001", "High Credit Utilization", "Credit utilization", 0.90, 0.95),
        ("B002", "Prolonged Overdraft", "Overdraft days", 10.0, 30.0),
        ("B003", "Payment Delay", "Payment delay days", 30.0, 60.0),
        ("B004", "Exposure Growth", "Exposure growth", 0.25, 0.40),
    )

    def __init__(self, status_calculator: AssessmentStatusCalculator | None = None):
        self.status_calculator = status_calculator or AssessmentStatusCalculator()

    def assess(self, data: BehaviouralData) -> AssessmentSection:
        results = [
            self._evaluate_rule(rule, value)
            for rule, value in zip(self._RULES, self._values(data), strict=True)
        ]
        findings = [
            RuleFinding(result=result, comment=Comment(result.rule_id, result.reason or ""))
            for result in results
            if result.status == RuleStatus.TRIGGERED
        ]

        return AssessmentSection(
            name="Behavioural Analysis",
            status=SectionStatus(self.status_calculator.calculate(results).value),
            findings=findings,
            evidence=results,
            limitations=[],
        )

    @staticmethod
    def _values(data: BehaviouralData) -> tuple[float | None, ...]:
        return (
            data.average_utilization,
            data.overdraft_days,
            data.payment_delay_days,
            data.exposure_growth,
        )

    @staticmethod
    def _evaluate_rule(
        rule: tuple[str, str, str, float, float],
        value: float | None,
    ) -> RuleResult:
        rule_id, rule_name, indicator, threshold, high_threshold = rule

        if value is None:
            return RuleResult(
                rule_id=rule_id,
                rule_name=rule_name,
                category="Behavioural Analysis",
                status=RuleStatus.NOT_EVALUABLE,
                value=None,
                threshold=threshold,
                severity=RuleSeverity.MEDIUM,
                reason=f"[{rule_id} - {rule_name}] Behavioural data are not available.",
                indicator=indicator,
                direction=SeverityDirection.HIGHER_IS_WORSE,
            )

        status = RuleStatus.TRIGGERED if value > threshold else RuleStatus.NOT_TRIGGERED
        severity = RuleSeverity.HIGH if value > high_threshold else RuleSeverity.MEDIUM
        reason = (
            f"[{rule_id} - {rule_name}] {indicator} is {value:.2f}, "
            f"above the threshold of {threshold:.2f}."
            if status == RuleStatus.TRIGGERED
            else f"[{rule_id} - {rule_name}] {indicator} is {value:.2f}, "
            f"within the threshold of {threshold:.2f}."
        )

        return RuleResult(
            rule_id=rule_id,
            rule_name=rule_name,
            category="Behavioural Analysis",
            status=status,
            value=value,
            threshold=threshold,
            severity=severity,
            reason=reason,
            indicator=indicator,
            direction=SeverityDirection.HIGHER_IS_WORSE,
        )
