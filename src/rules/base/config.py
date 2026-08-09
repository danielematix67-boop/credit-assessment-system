from dataclasses import dataclass

from src.rules.base.severity import RuleSeverity


@dataclass(frozen=True)
class RuleConfig:
    rule_id: str
    rule_name: str
    category: str
    threshold: float
    severity: RuleSeverity
