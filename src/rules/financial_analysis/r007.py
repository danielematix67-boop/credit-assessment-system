from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R007")
class InterestCoverageRatioRule(Rule):
    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
        ebitda = position.ebitda
        interest_expense = position.interest_expense

        if ebitda is None:
            return self._not_evaluable(reason="EBITDA is not available.")

        if interest_expense is None:
            return self._not_evaluable(
                reason="Interest expense is not available.",
            )

        if interest_expense <= 0:
            return self._not_evaluable(
                reason=(
                    "Interest expense must be greater than zero to calculate "
                    "the interest coverage ratio."
                ),
            )

        value, error = self._configured_value(position)

        if error is not None:
            return self._not_evaluable(reason=error)

        assert value is not None
        status = (
            RuleStatus.TRIGGERED
            if self._is_triggered(value)
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(value=value, status=status)
