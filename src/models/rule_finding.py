from dataclasses import dataclass
from src.comments.comment import Comment
from src.rules.result import RuleResult


@dataclass(frozen=True)
class RuleFinding:
    result: RuleResult
    comment: Comment