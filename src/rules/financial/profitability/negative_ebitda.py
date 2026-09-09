from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R002")
class NegativeEbitdaRule(Rule):
    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
        if position.ebitda is None:
            return self._not_evaluable(
                reason="EBITDA is not available.",
            )

        value = position.ebitda

        status = (
            RuleStatus.TRIGGERED
            if value < self.config.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
