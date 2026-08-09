from src.models.position import CreditPosition
from src.rules.result import RuleResult
from src.rules.base.rule import Rule

# Each rule should be implemented as a separate class with a unique rule_id.
#
# Multiple related rules can coexist in the same module, but each class should
# represent one specific business rule and return one RuleResult.


class PfnToEbitdaRule(Rule):

    rule_id = "R004"
    rule_name = "PFN / EBITDA leverage"
    category = "leverage"
    threshold = 5.0

    def evaluate(self, position: CreditPosition) -> RuleResult:

        if position.pfn_to_ebitda is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                category=self.category,
                triggered=False,
                value=None,
                threshold=self.threshold,
                status="NOT_EVALUABLE",
            )

        triggered = position.pfn_to_ebitda > self.threshold

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            triggered=triggered,
            value=position.pfn_to_ebitda,
            threshold=self.threshold,
            status="OK",
        )
