from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


# Each rule should be implemented as a separate class with a unique rule_id.
#
# Multiple related rules can coexist in the same module, but each class should
# represent one specific business rule and return one RuleResult.


class RevenueGrowthRule(Rule):

    rule_id = "R001"
    rule_name = "Revenue deterioration"
    category = "revenue"
    threshold = -0.10

    def evaluate(self, position: CreditPosition) -> RuleResult:

        if position.revenue_growth is None:
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
            if position.revenue_growth < self.threshold
            else RuleStatus.NOT_TRIGGERED
        )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            status=status,
            value=position.revenue_growth,
            threshold=self.threshold,
        )
