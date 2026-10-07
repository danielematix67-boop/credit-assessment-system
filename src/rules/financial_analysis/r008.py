from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R008")
class OperatingLeverageRule(Rule):
    """Evaluate operating leverage as contribution margin relative to EBIT."""

    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
        contribution_margin = position.contribution_margin
        ebit = position.net_operating_margin

        if contribution_margin is None:
            return self._not_evaluable(
                reason="Contribution margin is not available.",
            )

        if ebit is None:
            return self._not_evaluable(
                reason="EBIT is not available.",
            )

        if ebit <= 0:
            return self._not_evaluable(
                reason=(
                    "Operating leverage is not meaningful because EBIT is "
                    "negative or zero."
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

        return self._result(value=value, status=status)
