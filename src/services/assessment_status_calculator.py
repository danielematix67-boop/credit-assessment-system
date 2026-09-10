from src.models.assessment_status import AssessmentStatus
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class AssessmentStatusCalculator:
    def calculate(self, results: list[RuleResult]) -> AssessmentStatus:
        triggered_count = sum(
            result.status == RuleStatus.TRIGGERED for result in results
        )

        if triggered_count >= 2:
            return AssessmentStatus.CRITICAL

        if triggered_count == 1:
            return AssessmentStatus.ATTENTION

        # No triggered rule is not equivalent to a normal assessment when
        # none of the indicators could actually be evaluated.
        if results and all(
            result.status == RuleStatus.NOT_EVALUABLE for result in results
        ):
            return AssessmentStatus.ATTENTION

        return AssessmentStatus.NORMAL
