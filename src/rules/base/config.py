from dataclasses import dataclass

from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold

@dataclass(frozen=True)
class RuleConfig:
    rule_id: str
    rule_name: str
    category: str
    threshold: float
    severity: RuleSeverity
    severity_direction: SeverityDirection = (
        SeverityDirection.HIGHER_IS_WORSE
    )
    severity_thresholds: tuple[SeverityThreshold, ...] = ()