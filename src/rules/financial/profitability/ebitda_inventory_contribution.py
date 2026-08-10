from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R006")
class EbitdaInventoryContributionRule(Rule):

    def evaluate(self, position: CreditPosition) -> RuleResult:

        if (
            position.ebitda is None
            or position.change_in_finished_goods_inventory is None
            or position.ebitda <= 0
        ):
            return self._not_evaluable()

        value = (
            position.change_in_finished_goods_inventory
            / position.ebitda
        )

        status = (
            RuleStatus.TRIGGERED
            if value >= self.config.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
