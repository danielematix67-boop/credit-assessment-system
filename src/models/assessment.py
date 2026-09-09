from dataclasses import dataclass

from src.models.assessment_status import AssessmentStatus
from src.models.rule_finding import RuleFinding
from src.rules.result import RuleResult


@dataclass(frozen=True)
class Assessment:
    position_id: str
    rule_results: list[RuleResult]
    findings: list[RuleFinding]
    status: AssessmentStatus
