from dataclasses import dataclass

@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    category: str
    triggered: bool
    value: float
    threshold: float