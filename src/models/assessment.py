from dataclasses import dataclass

from src.comments.comment import Comment
from src.models.assessment_status import AssessmentStatus
from src.rules.result import RuleResult


@dataclass(frozen=True)
class Assessment:
    position_id: str
    rule_results: list[RuleResult]
    comments: list[Comment]
    status: AssessmentStatus