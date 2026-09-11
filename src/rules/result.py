from dataclasses import dataclass

from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
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
    indicator: str = ""
    direction: SeverityDirection = SeverityDirection.HIGHER_IS_WORSE
    comment_template: str = ""

    @property
    def is_triggered(self) -> bool:
        """Return whether the deterministic rule condition was triggered."""
        return self.status == RuleStatus.TRIGGERED
