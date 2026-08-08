from src.comments.comment import Comment
from src.comments.templates import COMMENTS
from src.rules.result import RuleResult


class CommentEngine:

    def generate(self, result: RuleResult) -> Comment | None:
        if not result.triggered:
            return None

        return COMMENTS.get(result.rule_id)