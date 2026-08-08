from src.comments.comment import Comment
from src.comments.templates import COMMENTS
from src.rules.result import RuleResult


class CommentEngine:

    def generate(self, result: RuleResult) -> Comment | None:
        if not result.triggered:
            return None

        template = COMMENTS.get(result.rule_id)

        if template is None:
            return None

        return Comment(
            rule_id=result.rule_id,
            text=template.format(
                value=result.value,
                threshold=result.threshold,
            ),
        )