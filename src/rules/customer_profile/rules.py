from typing import Any

from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class CustomerProfileRule(Rule):
    """Shared deterministic implementation for scalar customer-profile rules."""

    def evaluate(self, position: Any) -> RuleResult:
        value, error = self._configured_value(position)
        if error is not None:
            return self._not_evaluable(error)
        assert value is not None
        status = RuleStatus.TRIGGERED if self._is_triggered(value) else RuleStatus.NOT_TRIGGERED
        return self._result(value=value, status=status)


@Rule.register("CP001")
class ActiveEwsRule(CustomerProfileRule):
    """Evaluate the active Early Warning System flag."""


@Rule.register("CP002")
class PreviousRestructuringRule(CustomerProfileRule):
    """Evaluate the previous-restructuring flag."""


@Rule.register("CP003")
class BusinessHistoryRule(CustomerProfileRule):
    """Evaluate the customer's business-history length."""
