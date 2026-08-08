from dataclasses import dataclass

from src.comments.comment import Comment
from src.rules.result import RuleResult


@dataclass
class Assessment:
    position_id: str
    rule_results: list[RuleResult]
    comments: list[Comment]