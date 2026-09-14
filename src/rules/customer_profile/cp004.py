from typing import Any

from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("CP004")
class ForborneExposureRule(Rule):
    """Evaluate whether the customer has a forborne exposure."""

    def evaluate(self, position: Any) -> RuleResult:
        value = getattr(position, self.config.input_field, None)
        if value is None:
            return self._not_evaluable(
                f"Required input field is not available: {self.config.input_field}."
            )

        if not isinstance(value, bool):
            return self._not_evaluable(
                f"Invalid forborne flag: {value!r}. Expected a boolean value."
            )

        status = RuleStatus.TRIGGERED if value else RuleStatus.NOT_TRIGGERED
        severity = RuleSeverity.MEDIUM if value else RuleSeverity.LOW
        return self._result(
            value=value,
            status=status,
            severity=severity,
        )
