
from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class PfnToEbitdaRule(Rule):
    """
    Triggers when PFN / EBITDA exceeds the defined leverage threshold.
    """

    rule_id = "R004"
    rule_name = "PFN / EBITDA leverage"
    category = "leverage"
    threshold = 5.0

    def evaluate(self, position: CreditPosition) -> RuleResult:
        value = position.pfn_to_ebitda

        if value is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                category=self.category,
                status=RuleStatus.NOT_EVALUABLE,
                value=None,
                threshold=self.threshold,
            )

        status = (
            RuleStatus.TRIGGERED
            if value > self.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            status=status,
            value=value,
            threshold=self.threshold,
        )
