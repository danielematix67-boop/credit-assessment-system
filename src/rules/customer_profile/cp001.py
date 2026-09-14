from typing import Any

from src.models.ews_score import EwsScoreClass
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("CP001")
class EwsScoreClassRule(Rule):
    """Evaluate the EWS score colour class."""

    _SEVERITY_BY_CLASS = {
        EwsScoreClass.YELLOW: RuleSeverity.MEDIUM,
        EwsScoreClass.ORANGE: RuleSeverity.MEDIUM,
        EwsScoreClass.LIGHT_RED: RuleSeverity.HIGH,
    }

    def evaluate(self, position: Any) -> RuleResult:
        raw_value = getattr(position, self.config.input_field, None)
        if raw_value is None:
            return self._not_evaluable(
                "Required input field is not available: ews_score_class."
            )

        try:
            score_class = (
                raw_value
                if isinstance(raw_value, EwsScoreClass)
                else EwsScoreClass(raw_value)
            )
        except (TypeError, ValueError):
            return self._not_evaluable(
                f"Invalid EWS score class: {raw_value!r}."
            )

        severity = self._SEVERITY_BY_CLASS.get(score_class, RuleSeverity.LOW)
        triggered = score_class != EwsScoreClass.GREEN
        status = RuleStatus.TRIGGERED if triggered else RuleStatus.NOT_TRIGGERED

        reason = (
            f"EWS Score class is {score_class.value}; "
            + (
                "the colour class indicates an elevated credit-risk condition."
                if triggered
                else "the colour class does not indicate an elevated credit-risk condition."
            )
        )

        return self._result(
            value=None,
            status=status,
            reason=reason,
            severity=severity,
        )
