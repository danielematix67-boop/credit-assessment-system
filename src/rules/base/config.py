from dataclasses import dataclass


@dataclass(frozen=True)
class RuleConfig:
    rule_id: str
    rule_name: str
    category: str
    threshold: float