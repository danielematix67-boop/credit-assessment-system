from dataclasses import dataclass

from src.rules.base.status import RuleStatus


# RuleResult is the standardized output of a rule evaluation.
#
# It contains the rule identity, category, calculated value,
# threshold, and evaluation status.
#
# Downstream components should rely on RuleResult rather than
# accessing rule-specific logic.


@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    category: str
    status: RuleStatus
    value: float | None
    threshold: float
