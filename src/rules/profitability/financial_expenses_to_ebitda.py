from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus


class FinancialExpensesToEbitdaRule(Rule):
    """
    Triggers when interest expense exceeds the defined proportion of EBITDA.
    """

    rule_id = "R005"
    rule_name = "Interest expense to EBITDA"
    category = "profitability"
    threshold = 0.60

    def evaluate(self, position: CreditPosition):

        interest_expense = position.interest_expense
        ebitda = position.ebitda

        if interest_expense is None or ebitda is None or ebitda <= 0:
            return self._not_evaluable()

        value = interest_expense / ebitda

        status = (
            RuleStatus.TRIGGERED
            if value > self.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
