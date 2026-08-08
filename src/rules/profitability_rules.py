from src.models.position import CreditPosition
from src.rules.result import RuleResult
from src.rules.rule import Rule


class NegativeEbitdaRule(Rule):

    rule_id = "R002"
    rule_name = "Negative EBITDA"
    category = "profitability"
    threshold = 0

    def evaluate(self, position: CreditPosition) -> RuleResult:
        triggered = position.ebitda < self.threshold

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            triggered=triggered,
            value=position.ebitda,
            threshold=self.threshold,
        )