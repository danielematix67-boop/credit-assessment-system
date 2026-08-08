from src.models.position import CreditPosition
from src.rules.rule import Rule
from src.rules.result import RuleResult


class FinancialExpensesToEbitdaRule(Rule):

    def evaluate(self, position: CreditPosition) -> RuleResult:
        threshold = 0.60

        if position.interest_expense is None:
            return RuleResult(
                rule_id="R005",
                rule_name="Interest expense to EBITDA",
                category="profitability",
                triggered=False,
                value=0.0,
                threshold=threshold,
            )

        if position.ebitda <= 0:
            return RuleResult(
                rule_id="R005",
                rule_name="Interest expense to EBITDA",
                category="profitability",
                triggered=False,
                value=0.0,
                threshold=threshold,
            )

        value = position.interest_expense / position.ebitda

        return RuleResult(
            rule_id="R005",
            rule_name="Interest expense to EBITDA",
            category="profitability",
            triggered=value > threshold,
            value=value,
            threshold=threshold,
        )