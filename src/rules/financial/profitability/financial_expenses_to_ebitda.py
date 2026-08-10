from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R005")
class FinancialExpensesToEbitdaRule(Rule):
    """
    Triggers when interest expense exceeds the defined proportion of EBITDA.
    """

    def evaluate(self, position: CreditPosition) -> RuleResult:

        interest_expense = position.interest_expense
        ebitda = position.ebitda

        if interest_expense is None or ebitda is None or ebitda <= 0:
            return self._not_evaluable()

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
