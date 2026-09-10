from dataclasses import dataclass
from enum import Enum

from src.models.rule_finding import RuleFinding
from src.rules.result import RuleResult


class SectionStatus(Enum):
    NORMAL = "NORMAL"
    ATTENTION = "ATTENTION"
    CRITICAL = "CRITICAL"
    NOT_EVALUABLE = "NOT_EVALUABLE"


@dataclass(frozen=True)
class AssessmentSection:
    """Deterministic assessment of one macro-area of the credit analysis."""

    name: str
    status: SectionStatus
    findings: list[RuleFinding]
    evidence: list[RuleResult]
    limitations: list[str]

    @property
    def is_evaluable(self) -> bool:
        return self.status != SectionStatus.NOT_EVALUABLE
