from src.models.position import CreditPosition
from src.rules.rule import Rule
from src.rules.result import RuleResult


class EbitdaMarginRule(Rule):

    def evaluate(self, position: CreditPosition) -> RuleResult:
        threshold = 0.0
        triggered = position.ebitda_margin < threshold

        return RuleResult(
            rule_id="R003",
            rule_name="EBITDA margin deterioration",
            category="profitability",
            triggered=triggered,
            value=position.ebitda_margin,
            threshold=threshold,
        )