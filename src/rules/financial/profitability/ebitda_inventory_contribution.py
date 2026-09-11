from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R006")
class EbitdaInventoryContributionRule(Rule):
    """Evaluate EBITDA contribution from finished goods inventory changes."""

    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
        ebitda = position.ebitda
        inventory_change = position.change_in_finished_goods_inventory

        if ebitda is None:
            return self._not_evaluable(reason="EBITDA is not available.")

        if inventory_change is None:
            return self._not_evaluable(
                reason="Change in finished goods inventory is not available.",
            )

        if ebitda <= 0:
            return self._not_evaluable(
                reason=(
                    "EBITDA must be greater than zero to calculate the "
                    "inventory contribution to EBITDA."
                ),
            )

        value, error = self._configured_value(position)

        if error is not None:
            return self._not_evaluable(reason=error)

        assert value is not None
        status = (
            RuleStatus.TRIGGERED
            if self._is_triggered(value)
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
