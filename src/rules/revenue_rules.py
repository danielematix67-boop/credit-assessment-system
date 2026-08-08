from src.models.position import CreditPosition
from src.rules.result import RuleResult
from src.rules.rule import Rule


class RevenueGrowthRule(Rule):

    def evaluate(self, position: CreditPosition) -> RuleResult:
        threshold = -0.10

        return RuleResult(
            rule_id="R001",
            rule_name="Revenue deterioration",
            category="revenue",
            triggered=position.revenue_growth < threshold,
            value=position.revenue_growth,
            threshold=threshold,
        )