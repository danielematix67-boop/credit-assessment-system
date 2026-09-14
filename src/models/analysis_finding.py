from dataclasses import dataclass

from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus


@dataclass(frozen=True)
class AnalysisFinding:
    rule_id: str
    category: str
    severity: RuleSeverity
    text: str
    status: RuleStatus | None = None
    assessment_area: str | None = None
