from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus


# Each rule represents one independent business rule.
#
# A rule evaluates a CreditPosition and returns exactly one RuleResult.
#
# Related rules may live in the same module, but each rule must have
# its own configuration.


class NegativeEbitdaRule(Rule):

    def evaluate(self, position: CreditPosition):

        if position.ebitda is None:
            return self._not_evaluable()

        value = position.ebitda

        status = (
            RuleStatus.TRIGGERED
            if value < self.config.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
