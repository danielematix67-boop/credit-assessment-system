from src.rules.base.rule import Rule


@Rule.register("CP001")
class ActiveEwsRule(Rule):
    """Evaluate the active Early Warning System flag."""

    def evaluate(self, position):
        value, error = self._configured_value(position)
        if error is not None:
            return self._not_evaluable(error)
        assert value is not None
        return self._result(
            value=value,
            status=self._trigger_status(value),
        )

    def _trigger_status(self, value):
        from src.rules.base.status import RuleStatus

        return RuleStatus.TRIGGERED if self._is_triggered(value) else RuleStatus.NOT_TRIGGERED


@Rule.register("CP002")
class PreviousRestructuringRule(ActiveEwsRule):
    """Evaluate the previous-restructuring flag."""


@Rule.register("CP003")
class BusinessHistoryRule(ActiveEwsRule):
    """Evaluate the customer's business-history length."""
