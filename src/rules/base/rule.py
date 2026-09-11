from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import ClassVar

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_policy import SeverityPolicy
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class Rule(ABC):
    _registry: ClassVar[dict[str, type["Rule"]]] = {}

    def __init__(
        self,
        config: RuleConfig,
    ):
        self.config = config

        self._severity_policy = SeverityPolicy(
            direction=config.severity_direction,
            thresholds=config.severity_thresholds,
        )

    @abstractmethod
    def evaluate(
        self,
        position: CreditPosition,
    ) -> RuleResult:
        """Evaluate the rule against a credit position."""
        pass

    def _configured_value(
        self,
        position: CreditPosition,
    ) -> tuple[float | None, str | None]:
        """Resolve and calculate a numeric value from rule configuration."""
        fields = self.config.input_fields or ((self.config.input_field,) if self.config.input_field else ())

        if not fields:
            return None, "No input field is configured."

        values: list[float | None] = [getattr(position, field, None) for field in fields]

        if any(value is None for value in values):
            return None, f"Required input field is not available: {', '.join(fields)}."

        numeric_values = [float(value) for value in values if value is not None]

        if self.config.calculation == "direct":
            if len(numeric_values) != 1:
                return None, "Direct calculation requires exactly one input field."
            return numeric_values[0], None

        if len(numeric_values) != 2:
            return None, f"{self.config.calculation} calculation requires exactly two input fields."

        numerator, denominator = numeric_values
        if self.config.calculation == "ratio":
            if denominator == 0:
                return None, "Ratio denominator cannot be zero."
            return numerator / denominator, None

        if self.config.calculation == "difference":
            return numerator - denominator, None

        return None, f"Unsupported calculation: {self.config.calculation}."

    def _is_triggered(
        self,
        value: float,
    ) -> bool:
        """Apply the configured trigger operator to a calculated value."""
        threshold = self.config.threshold
        operators: dict[str, Callable[[float, float], bool]] = {
            "GT": lambda left, right: left > right,
            "GTE": lambda left, right: left >= right,
            "LT": lambda left, right: left < right,
            "LTE": lambda left, right: left <= right,
        }
        return operators[self.config.trigger_operator](value, threshold)

    def _severity(
        self,
        value: float,
    ) -> RuleSeverity:
        """Resolve severity through the configured SeverityPolicy."""
        resolved_severity = self._severity_policy.evaluate(value)
        if resolved_severity is None:
            return self.config.severity
        return resolved_severity

    def _format_reason(
        self,
        reason: str | None,
    ) -> str:
        """Add the deterministic rule reference to the reason."""
        rule_reference = f"[{self.config.rule_id} - {self.config.rule_name}]"
        if reason is None:
            return f"{rule_reference} Rule evaluation completed."
        return f"{rule_reference} {reason}"

    def _result(
        self,
        *,
        value: float | None,
        status: RuleStatus,
        reason: str | None = None,
        severity: RuleSeverity | None = None,
    ) -> RuleResult:
        """Build a deterministic RuleResult with configured metadata."""
        if severity is not None:
            resolved_severity = severity
        elif value is not None:
            resolved_severity = self._severity(value)
        else:
            resolved_severity = self.config.severity

        return RuleResult(
            rule_id=self.config.rule_id,
            rule_name=self.config.rule_name,
            category=self.config.category,
            status=status,
            value=value,
            threshold=self.config.threshold,
            severity=resolved_severity,
            reason=self._format_reason(reason),
            indicator=self.config.indicator or self.config.rule_name,
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
        """Register a concrete Rule implementation."""
        def decorator(rule_class: type["Rule"]) -> type["Rule"]:
            if rule_id in cls._registry:
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
