from src.comments.comment_engine import CommentEngine
from src.models.rule_finding import RuleFinding
from src.rules.result import RuleResult


class FindingEngine:

    def __init__(self, comment_engine: CommentEngine):
        self.comment_engine = comment_engine

    def generate(self, result: RuleResult) -> RuleFinding | None:
        comment = self.comment_engine.generate(result)

        if comment is None:
            return None

        return RuleFinding(
            result=result,
            comment=comment,
        )