from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


# Each rule represents one independent business rule.
#
# The rule evaluates revenue growth against the configured threshold
# and returns a standardized RuleResult.


class RevenueGrowthRule(Rule):

    def evaluate(self, position: CreditPosition) -> RuleResult:

        value = position.revenue_growth

        if value is None:
            return self._not_evaluable()

        status = (
            RuleStatus.TRIGGERED
            if value < self.config.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
