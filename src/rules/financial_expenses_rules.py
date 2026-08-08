from src.models.position import CreditPosition
from src.rules.rule import Rule
from src.rules.result import RuleResult

# Each rule should be implemented as a separate class with a unique rule_id.
#
# Multiple related rules can coexist in the same module, but each class should
# represent one specific business rule and return one RuleResult.


class FinancialExpensesToEbitdaRule(Rule):

    rule_id = "R005"
    rule_name = "Interest expense to EBITDA"
    category = "profitability"
    threshold = 0.60

    def evaluate(self, position: CreditPosition) -> RuleResult:

        if position.interest_expense is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                category=self.category,
                triggered=False,
                value=None,
                threshold=self.threshold,
                status="NOT_EVALUABLE",
            )

        if position.ebitda is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                category=self.category,
                triggered=False,
                value=None,
                threshold=self.threshold,
                status="NOT_EVALUABLE",
            )

        if position.ebitda <= 0:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                category=self.category,
                triggered=False,
                value=None,
                threshold=self.threshold,
                status="NOT_EVALUABLE",
            )

        value = position.interest_expense / position.ebitda

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            triggered=value > self.threshold,
            value=value,
            threshold=self.threshold,
            status="OK",
        )
