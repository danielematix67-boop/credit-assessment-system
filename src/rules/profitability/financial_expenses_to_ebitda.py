from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class FinancialExpensesToEbitdaRule(Rule):
    """
    Triggers when interest expense exceeds the defined proportion of EBITDA.
    """

    rule_id = "R005"
    rule_name = "Interest expense to EBITDA"
    category = "profitability"
    threshold = 0.60

    def evaluate(self, position: CreditPosition) -> RuleResult:
        interest_expense = position.interest_expense
        ebitda = position.ebitda

        if interest_expense is None or ebitda is None or ebitda <= 0:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                category=self.category,
                status=RuleStatus.NOT_EVALUABLE,
                value=None,
                threshold=self.threshold,
            )

        value = interest_expense / ebitda

        status = (
            RuleStatus.TRIGGERED
            if value > self.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            status=status,
            value=value,
            threshold=self.threshold,
        )
