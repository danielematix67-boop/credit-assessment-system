from dataclasses import dataclass

from src.rules.base.severity import RuleSeverity


@dataclass(frozen=True)
class AnalysisFinding:
    rule_id: str
    category: str
    severity: RuleSeverity
    text: str
