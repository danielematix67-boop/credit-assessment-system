from dataclasses import dataclass

from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus



# RuleResult is the standardized output of a rule evaluation.
#
# It contains the rule identity, category, calculated value,
# threshold, and evaluation status.
#
# RuleResult is immutable: once a rule evaluation has been completed,
# its result cannot be modified by downstream components.
#
# Downstream components should rely on RuleResult rather than
# accessing rule-specific logic.



@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    rule_name: str
    category: str
    status: RuleStatus
    value: float | None
    threshold: float
    severity: RuleSeverity


