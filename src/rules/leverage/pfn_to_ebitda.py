from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus


class PfnToEbitdaRule(Rule):
    """
    Triggers when PFN / EBITDA exceeds the defined leverage threshold.
    """

    rule_id = "R004"
    rule_name = "PFN / EBITDA leverage"
    category = "leverage"
    threshold = 5.0

    def evaluate(self, position: CreditPosition):

        value = position.pfn_to_ebitda

        if value is None:
            return self._not_evaluable()

        status = (
            RuleStatus.TRIGGERED
            if value > self.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return self._result(
            value=value,
            status=status,
        )
