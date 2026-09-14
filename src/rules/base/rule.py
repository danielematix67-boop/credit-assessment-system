from abc import ABC, abstractmethod
from typing import Callable, ClassVar

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class Rule(ABC):
    """Base class for deterministic credit-assessment rules."""

    _registry: ClassVar[dict[str, type["Rule"]]] = {}

    def __init__(self, config: RuleConfig) -> None:
        self.config = config

    @abstractmethod
    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
        """Evaluate the rule against a credit position."""
        raise NotImplementedError

    def _configured_value(
        self,
        position: CreditPosition,
    ) -> tuple[float | None, str | None]:
        """Resolve a rule value from its configured input field(s)."""
        fields = self.config.input_fields
        if not fields and self.config.input_field:
            fields = (self.config.input_field,)

        if not fields:
            return None, "No input field is configured for this rule."

        values: list[float] = []
        for field in fields:
            raw_value = getattr(position, field, None)
            if raw_value is None:
                return None, f"Required input field is not available: {field}."
            if not isinstance(raw_value, (int, float)):
                return None, f"{field} is not numeric."
            values.append(float(raw_value))

        if self.config.calculation == "direct":
            if len(values) != 1:
                return None, "Direct calculation requires exactly one input field."
            return values[0], None

        if len(values) != 2:
            return None, (
                f"{self.config.calculation} calculation requires exactly "
                "two input fields."
            )

        numerator, denominator = values
        if self.config.calculation == "ratio":
            if denominator == 0:
                return None, "Ratio denominator cannot be zero."
            return numerator / denominator, None

        if self.config.calculation == "difference":
            return numerator - denominator, None

        return None, f"Unsupported calculation: {self.config.calculation}."

    def _is_triggered(self, value: float) -> bool:
        """Evaluate the configured trigger operator against the threshold."""
        threshold = self.config.threshold
        operators: dict[str, Callable[[float, float], bool]] = {
            "GT": lambda current, limit: current > limit,
            "GTE": lambda current, limit: current >= limit,
            "LT": lambda current, limit: current < limit,
            "LTE": lambda current, limit: current <= limit,
        }
        return operators[self.config.trigger_operator](value, threshold)

    def _severity(self, value: float) -> RuleSeverity:
        """Resolve severity from configured severity thresholds."""
        thresholds = self.config.severity_thresholds
        if not thresholds:
            return self.config.severity

        if self.config.severity_direction.value == "HIGHER_IS_WORSE":
            # Values below the first configured band are on the safe side
            # of the rule and therefore explicitly LOW.
            severity = RuleSeverity.LOW
            for threshold in thresholds:
                if value >= threshold.threshold:
                    severity = threshold.severity
            return severity

        # For LOWER_IS_WORSE, the configured rule-level severity is the
        # baseline for values above the first risk band. More severe bands
        # are then selected as the value crosses their thresholds.
        severity = self.config.severity
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

    def _qualify_reason(self, reason: str) -> str:
        """Add a stable rule reference to non-template reasons."""
        return f"[{self.config.rule_id} - {self.config.rule_name}] {reason}"

    def _result(
        self,
        *,
        value: float | None,
        status: RuleStatus,
        reason: str | None = None,
        severity: RuleSeverity | None = None,
    ) -> RuleResult:
        """Build a RuleResult from the configured rule metadata."""
        resolved_reason = reason
        if resolved_reason is None and value is not None:
            resolved_reason = self._format_reason(value)
        if resolved_reason is None:
            resolved_reason = "Rule evaluation completed."

        if reason is not None or not self.config.comment_template:
            resolved_reason = self._qualify_reason(resolved_reason)

        resolved_severity = severity
        if resolved_severity is None:
            resolved_severity = self.config.severity
            if value is not None:
                resolved_severity = self._severity(value)

        return RuleResult(
            rule_id=self.config.rule_id,
            rule_name=self.config.rule_name,
            category=self.config.category,
            value=value,
            threshold=self.config.threshold,
            status=status,
            severity=resolved_severity,
            reason=resolved_reason,
            direction=self.config.severity_direction,
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
