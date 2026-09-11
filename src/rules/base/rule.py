from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class Rule(ABC):
    """Base class for deterministic credit-assessment rules."""

    _registry: ClassVar[dict[str, type["Rule"]]] = {}

    def __init__(self, config: RuleConfig) -> None:
        self.config = config

    @abstractmethod
    def evaluate(self, position: CreditPosition) -> RuleResult:
        """Evaluate the rule against a credit position."""
        raise NotImplementedError

    def _is_triggered(self, value: float) -> bool:
        """Evaluate the configured trigger threshold."""
        return value > self.config.threshold

    def _severity(self, value: float) -> Any:
        """Resolve severity from configured severity thresholds."""
        thresholds = self.config.severity_thresholds
        if not thresholds:
            return self.config.severity

        if self.config.severity_direction.value == "higher_is_worse":
            severity = thresholds[0].severity
            for threshold in thresholds:
                if value >= threshold.threshold:
                    severity = threshold.severity
            return severity

        severity = thresholds[0].severity
        for threshold in thresholds:
            if value <= threshold.threshold:
                severity = threshold.severity
        return severity

    def _format_reason(self, value: float) -> str | None:
        """Format the configured rule comment template, when available."""
        template = self.config.comment_template
        if not template:
            return None
        return template.format(value=value, threshold=self.config.threshold)

    def _result(
        self,
        *,
        value: float | None,
        status: RuleStatus,
        reason: str | None = None,
    ) -> RuleResult:
        """Build a RuleResult from the configured rule metadata."""
        resolved_reason = reason
        if resolved_reason is None and value is not None:
            resolved_reason = self._format_reason(value)

        severity = self.config.severity
        if value is not None:
            severity = self._severity(value)

        return RuleResult(
            rule_id=self.config.rule_id,
            rule_name=self.config.rule_name,
            category=self.config.category,
            value=value,
            threshold=self.config.threshold,
            status=status,
            severity=severity,
            reason=resolved_reason,
            comment_template=self.config.comment_template,
        )

    def _not_evaluable(
        self,
        reason: str,
    ) -> RuleResult:
        """Build a NOT_EVALUABLE RuleResult."""
        return self._result(
            value=None,
            status=RuleStatus.NOT_EVALUABLE,
            reason=reason,
        )

    @classmethod
    def register(
        cls,
        rule_id: str,
    ) -> Callable[[type["Rule"]], type["Rule"]]:
        """Register a concrete Rule implementation idempotently."""
        def decorator(rule_class: type["Rule"]) -> type["Rule"]:
            existing_rule = cls._registry.get(rule_id)
            if existing_rule is not None:
                if existing_rule is rule_class:
                    return rule_class

                # Test collection and module reloading can create a second
                # class object for the same source declaration. Treat that as
                # the same implementation while still rejecting a genuinely
                # different class claiming the same rule id.
                if (
                    existing_rule.__module__ == rule_class.__module__
                    and existing_rule.__qualname__ == rule_class.__qualname__
                ):
                    return existing_rule

                raise ValueError(f"Rule already registered: {rule_id}")
            cls._registry[rule_id] = rule_class
            return rule_class

        return decorator

    @classmethod
    def get_registered_rule(
        cls,
        rule_id: str,
    ) -> type["Rule"]:
        """Retrieve the concrete Rule class associated with a rule_id."""
        try:
            return cls._registry[rule_id]
        except KeyError:
            raise ValueError(f"Unknown rule_id: {rule_id}") from None
