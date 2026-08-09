from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus

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

    def evaluate(self, position: CreditPosition):

        if position.ebitda is None:
            return self._not_evaluable()

        value = position.ebitda

        status = (
            RuleStatus.TRIGGERED
            if value < self.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
