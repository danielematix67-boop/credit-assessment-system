from dataclasses import dataclass

from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    rule_name: str
    category: str
    status: RuleStatus
    value: float | None
    threshold: float
    severity: RuleSeverity
    reason: str | None = None
