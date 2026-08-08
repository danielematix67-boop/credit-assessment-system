from dataclasses import dataclass

# RuleResult is the standardized output of a rule evaluation.
# It contains the rule identity, category, calculated value, threshold, and trigger status.
# Downstream components should rely on RuleResult rather than accessing rule-specific logic.

@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    category: str
    triggered: bool
    value: float | None
    threshold: float
    status: str