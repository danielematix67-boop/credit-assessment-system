from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


# Each rule represents one independent business rule.
#
# A rule evaluates a CreditPosition and returns exactly one RuleResult.
#
# Related rules may live in the same module, but each rule must have
# its own class and rule_id.


class NegativeEbitdaRule(Rule):

    rule_id = "R002"
    rule_name = "Negative EBITDA"
    category = "profitability"
    threshold = 0

    def evaluate(self, position: CreditPosition) -> RuleResult:

        if position.ebitda is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                category=self.category,
                status=RuleStatus.NOT_EVALUABLE,
                value=None,
                threshold=self.threshold,
            )

        status = (
            RuleStatus.TRIGGERED
            if position.ebitda < self.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            status=status,
            value=position.ebitda,
            threshold=self.threshold,
        )
