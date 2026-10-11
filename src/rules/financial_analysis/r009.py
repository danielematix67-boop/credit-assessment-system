from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R009")
class OperatingGrantsIncidenceRule(Rule):
    """Assess operating grants as a share of total production value."""

    def evaluate(self, position: CreditPosition) -> RuleResult:
        grants = position.operating_grants
        production_value = position.production_value

        if grants is None:
            return self._not_evaluable(
                reason="Operating grants are not available.",
            )

        if production_value is None:
            return self._not_evaluable(
                reason="Total production value is not available.",
            )

        if production_value <= 0:
            return self._not_evaluable(
                reason="Total production value must be positive.",
            )

        if grants < 0:
            return self._not_evaluable(
                reason="Operating grants cannot be negative for this indicator.",
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
        return self._result(value=value, status=status)
