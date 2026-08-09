from abc import ABC, abstractmethod

from src.models.position import CreditPosition
from src.rules.result import RuleResult

# Each rule represents one independent business rule.
# A rule evaluates a CreditPosition and returns exactly one RuleResult.
# Related rules may live in the same module, but each rule must have its own class and rule_id.

class Rule(ABC):

    @abstractmethod
    def evaluate(self, position: CreditPosition) -> RuleResult:
        pass