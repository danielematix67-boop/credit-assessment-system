from abc import ABC, abstractmethod

from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


# Each rule represents one independent business rule.
#
# A rule evaluates a CreditPosition and returns exactly one RuleResult.
# Related rules may live in the same module, but each rule must have its
# own class and rule_id.
#
# The base class provides common helpers for building standardized
# RuleResult objects, while the concrete rule remains responsible for
# its own business logic.


class Rule(ABC):

    @abstractmethod
    def evaluate(self, position: CreditPosition) -> RuleResult:
        pass

    def _result(
        self,
        *,
        value: float | None,
        status: RuleStatus,
    ) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            status=status,
            value=value,
            threshold=self.threshold,
        )

    def _not_evaluable(self) -> RuleResult:
        return self._result(
            value=None,
            status=RuleStatus.NOT_EVALUABLE,
        )
