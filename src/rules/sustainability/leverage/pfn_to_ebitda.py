from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R004")
class PfnToEbitdaRule(Rule):
    """
    Triggers when PFN / EBITDA exceeds the defined leverage threshold.
    """

    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:

        value = position.pfn_to_ebitda

        if value is None:
            return self._not_evaluable(
                reason=(
                    "PFN / EBITDA is not available."
                ),
            )

        status = (
            RuleStatus.TRIGGERED
            if value > self.config.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )