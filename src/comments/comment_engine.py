from src.comments.comment import Comment
from src.comments.templates import COMMENTS
from src.rules.result import RuleResult


# The CommentEngine converts triggered RuleResults into human-readable comments.
# Rules determine whether a condition is triggered; the CommentEngine determines how it is communicated.
# Comment generation must remain separate from rule evaluation.

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