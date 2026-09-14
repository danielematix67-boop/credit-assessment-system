from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R005")
class FinancialExpensesToEbitdaRule(Rule):
    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
        if position.ebitda is None:
            return self._not_evaluable(reason="EBITDA is not available.")

        if position.ebitda <= 0:
            return self._not_evaluable(
                reason=(
                    "Interest expense to EBITDA ratio is not meaningful because "
                    "EBITDA is negative or zero. Interest expenses cannot be "
                    "covered by operating profitability."
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
