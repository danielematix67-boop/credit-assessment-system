from typing import Any

from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class DebtSustainabilityRule(Rule):
    """Shared deterministic implementation for debt-sustainability rules."""

    def evaluate(self, position: Any) -> RuleResult:
        value, error = self._configured_value(position)
        if error is not None:
            return self._not_evaluable(error)
        assert value is not None
        status = (
            RuleStatus.TRIGGERED
            if self._is_triggered(value)
            else RuleStatus.NOT_TRIGGERED
        )
        return self._result(value=value, status=status)


@Rule.register("DS001")
class DebtServiceCoverageRatioRule(DebtSustainabilityRule):
    """Evaluate debt-service coverage ratio."""


@Rule.register("DS002")
class DebtServiceToEbitdaRule(DebtSustainabilityRule):
    """Evaluate debt service relative to EBITDA."""


@Rule.register("DS003")
class CashFlowDebtServiceBufferRule(DebtSustainabilityRule):
    """Evaluate the CFADS debt-service buffer."""
