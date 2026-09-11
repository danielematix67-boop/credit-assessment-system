from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R003")
class EbitdaMarginRule(Rule):
    """
    Triggers when EBITDA margin falls below the configured threshold.

    The value and trigger semantics are resolved from rule configuration.
    The rule is not evaluable when the configured input is unavailable.
    """

    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
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
