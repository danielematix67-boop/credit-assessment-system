
from src.models.position import CreditPosition
from src.rules.result import RuleResult
from src.rules.rule import Rule

# Each rule should be implemented as a separate class with a unique rule_id.
#
# Multiple related rules can coexist in the same module, but each class should
# represent one specific business rule and return one RuleResult.


class EbitdaMarginRule(Rule):

    rule_id = "R003"
    rule_name = "EBITDA margin deterioration"
    category = "profitability"
    threshold = 0.0

    def evaluate(self, position: CreditPosition) -> RuleResult:

        if position.ebitda_margin is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                category=self.category,
                triggered=False,
                value=None,
                threshold=self.threshold,
                status="NOT_EVALUABLE",
            )

        triggered = position.ebitda_margin < self.threshold

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            triggered=triggered,
            value=position.ebitda_margin,
            threshold=self.threshold,
            status="OK",
        )
