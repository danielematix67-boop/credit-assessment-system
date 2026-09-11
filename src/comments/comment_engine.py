from src.comments.comment import Comment
from src.comments.templates import COMMENTS
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class CommentEngine:
    """Convert deterministic rule results into human-readable comments."""

    def generate(
        self,
        result: RuleResult,
    ) -> Comment | None:
        if result.status != RuleStatus.TRIGGERED:
            return None

        template = result.comment_template or COMMENTS.get(result.rule_id)
        if template is None:
            return None

        return Comment(
            rule_id=result.rule_id,
            text=template.format(value=result.value),
        )
