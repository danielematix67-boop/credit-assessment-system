from src.models.position import CreditPosition
from src.rules.result import RuleResult
from src.rules.rule import Rule


class RevenueGrowthRule(Rule):

    rule_id = "R001"
    rule_name = "Revenue deterioration"
    category = "revenue"
    threshold = -0.10

    def evaluate(self, position: CreditPosition) -> RuleResult:
        triggered = position.revenue_growth < self.threshold

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            triggered=triggered,
            value=position.revenue_growth,
            threshold=self.threshold,
        )