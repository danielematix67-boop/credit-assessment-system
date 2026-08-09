from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


# Each rule represents one independent business rule.
#
# The rule evaluates revenue growth against the configured threshold
# and returns a standardized RuleResult.

class RevenueGrowthRule(Rule):

    rule_id = "R001"
    rule_name = "Revenue deterioration"
    category = "revenue"
    threshold = -0.10

    def evaluate(self, position: CreditPosition) -> RuleResult:

        if position.revenue_growth is None:
            return self._not_evaluable()

        value = position.revenue_growth

        status = (
            RuleStatus.TRIGGERED
            if value < self.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
