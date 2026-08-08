from src.comments.comment import Comment
from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition


class AssessmentService:

    def __init__(
        self,
        rule_engine: RuleEngine,
        comment_engine: CommentEngine,
    ):
        self.rule_engine = rule_engine
        self.comment_engine = comment_engine

    def assess(self, position: CreditPosition) -> list[Comment]:
        results = self.rule_engine.evaluate(position)

        comments = []

        for result in results:
            comment = self.comment_engine.generate(result)

            if comment is not None:
                comments.append(comment)

        return comments