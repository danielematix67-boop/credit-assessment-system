from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R001")
class RevenueGrowthRule(Rule):

    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:

        value = position.revenue_growth

        if value is None:

            return self._not_evaluable(
                reason=(
                    "Revenue growth is not available."
                ),
            )

        status = (
            RuleStatus.TRIGGERED
            if value < self.config.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )