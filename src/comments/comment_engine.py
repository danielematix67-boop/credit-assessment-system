from src.comments.comment import Comment
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class CommentEngine:
    """Convert deterministic rule results into configured comments.

    Comment text is supplied by the rule configuration and carried through
    ``RuleResult``. This keeps business-policy text outside Python code and
    ensures the same deterministic comments are available to the reporting
    fallback without maintaining a second template catalogue.
    """

    def generate(
        self,
        result: RuleResult,
    ) -> Comment | None:
        if result.status != RuleStatus.TRIGGERED:
            return None

        if not result.comment_template:
            return None

        return Comment(
            rule_id=result.rule_id,
            text=result.comment_template.format(value=result.value),
        )
