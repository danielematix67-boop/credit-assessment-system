from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


# Each rule should be implemented as a separate class with a unique rule_id.
#
# Multiple related rules can coexist in the same module, but each class should
# represent one specific business rule and return one RuleResult.


class PfnToEbitdaRule(Rule):

    rule_id = "R004"
    rule_name = "PFN / EBITDA leverage"
    category = "leverage"
    threshold = 5.0

    def evaluate(self, position: CreditPosition) -> RuleResult:

        if position.pfn_to_ebitda is None:
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
            if position.pfn_to_ebitda > self.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            status=status,
            value=position.pfn_to_ebitda,
            threshold=self.threshold,
        )
