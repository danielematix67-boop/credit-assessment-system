from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R006")
class EbitdaInventoryContributionRule(Rule):
    """
    Triggers when the contribution of the change in finished
    goods inventory to EBITDA exceeds the defined threshold.

    The rule is not evaluable when EBITDA or the inventory
    variation is missing, or when EBITDA is not positive.
    """

    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
        ebitda = position.ebitda
        inventory_change = position.change_in_finished_goods_inventory

        if ebitda is None:
            return self._not_evaluable(
                reason="EBITDA is not available.",
            )

        if inventory_change is None:
            return self._not_evaluable(
                reason=("Change in finished goods inventory is not available."),
            )

        if ebitda <= 0:
            return self._not_evaluable(
                reason=(
                    "EBITDA must be greater than zero "
                    "to calculate the inventory contribution "
                    "to EBITDA."
                ),
            )

        value = inventory_change / ebitda

        status = (
            RuleStatus.TRIGGERED
            if value >= self.config.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
