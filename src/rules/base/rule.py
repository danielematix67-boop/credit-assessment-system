from abc import ABC, abstractmethod
from typing import ClassVar

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class Rule(ABC):

    _registry: ClassVar[dict[str, type["Rule"]]] = {}

    def __init__(self, config: RuleConfig):
        self.config = config

    @abstractmethod
    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
        pass

    def _result(
        self,
        *,
        value: float | None,
        status: RuleStatus,
        reason: str | None = None,
    ) -> RuleResult:

        return RuleResult(
            rule_id=self.config.rule_id,
            rule_name=self.config.rule_name,
            category=self.config.category,
            status=status,
            value=value,
            threshold=self.config.threshold,
            severity=self.config.severity,
            reason=reason,
        )

    def _not_evaluable(
        self,
        reason: str,
    ) -> RuleResult:

        return self._result(
            value=None,
            status=RuleStatus.NOT_EVALUABLE,
            reason=reason,
        )

    @classmethod
    def register(
        cls,
        rule_id: str,
    ):

        def decorator(
            rule_class: type["Rule"],
        ) -> type["Rule"]:

            if rule_id in cls._registry:
                raise ValueError(
                    f"Rule already registered: {rule_id}"
                )

            cls._registry[rule_id] = rule_class

            return rule_class

        return decorator

    @classmethod
    def get_registered_rule(
        cls,
        rule_id: str,
    ) -> type["Rule"]:

        try:
            return cls._registry[rule_id]

        except KeyError:

            raise ValueError(
                f"Unknown rule_id: {rule_id}"
            ) from None