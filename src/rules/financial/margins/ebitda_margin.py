from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R003")
class EbitdaMarginRule(Rule):
    """
    Triggers when EBITDA margin falls below the configured threshold.

    The EBITDA margin is provided directly by CreditPosition.
    The rule is responsible only for evaluating the value against
    the configured business threshold.

    The rule is not evaluable when EBITDA margin is missing.
    """

    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
        value = position.ebitda_margin

        if value is None:
            return self._not_evaluable(
                reason="EBITDA margin is not available.",
            )

        status = (
            RuleStatus.TRIGGERED
            if value < self.config.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
