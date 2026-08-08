from src.models.position import CreditPosition
from src.rules.result import RuleResult
from src.rules.rule import Rule


class RuleEngine:

    def __init__(self, rules: list[Rule]):
        self.rules = rules

    def evaluate(self, position: CreditPosition) -> list[RuleResult]:
        results = []

        for rule in self.rules:
            results.append(rule.evaluate(position))

        return results