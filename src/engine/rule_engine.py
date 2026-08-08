from src.models.position import CreditPosition
from src.rules.result import RuleResult
from src.rules.rule import Rule

# The RuleEngine is responsible only for executing the registered rules.
# It should not contain business-rule logic or generate comments.
# Each registered rule produces one RuleResult.

class RuleEngine:

    def __init__(self, rules: list[Rule]):
        self.rules = rules

    def evaluate(self, position: CreditPosition) -> list[RuleResult]:
        results = []

        for rule in self.rules:
            results.append(rule.evaluate(position))

        return results