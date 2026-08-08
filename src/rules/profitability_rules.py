from src.models.position import CreditPosition
from src.rules.result import RuleResult
from src.rules.rule import Rule


class NegativeEbitdaRule(Rule):

    def evaluate(self, position: CreditPosition) -> RuleResult:
        threshold = 0

        return RuleResult(
            rule_id="R002",
            rule_name="Negative EBITDA",
            category="profitability",
            triggered=position.ebitda < threshold,
            value=position.ebitda,
            threshold=threshold,
        )