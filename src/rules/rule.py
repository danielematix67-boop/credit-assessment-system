from abc import ABC, abstractmethod

from src.models.position import CreditPosition
from src.rules.result import RuleResult


class Rule(ABC):

    @abstractmethod
    def evaluate(self, position: CreditPosition) -> RuleResult:
        pass