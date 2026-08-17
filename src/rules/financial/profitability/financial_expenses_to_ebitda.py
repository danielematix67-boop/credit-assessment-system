from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R005")
class FinancialExpensesToEbitdaRule(Rule):
    """
    Triggers when interest expense exceeds the defined proportion
    of EBITDA.
    """

    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:

        interest_expense = position.interest_expense
        ebitda = position.ebitda

        if interest_expense is None:
            return self._not_evaluable(
                reason="Interest expense is not available.",
            )

        if ebitda is None:
            return self._not_evaluable(
                reason="EBITDA is not available.",
            )

        if ebitda <= 0:
            return self._not_evaluable(
                reason=(
                    "Interest expense to EBITDA ratio is not meaningful because EBITDA is negative or zero."
                    " Interest expenses cannot be covered by operating profitability."
                ),
            )

        value = interest_expense / ebitda

        status = (
            RuleStatus.TRIGGERED
            if value > self.config.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )