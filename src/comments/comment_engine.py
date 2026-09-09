from src.comments.comment import Comment
from src.comments.templates import COMMENTS
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult

# The CommentEngine converts triggered rule results into human-readable comments.
# Rules are responsible for evaluating business conditions and assigning a
# RuleStatus. The CommentEngine is responsible only for translating triggered
# results into human-readable comments.
# Comment generation must remain separate from rule evaluation and business logic.


class CommentEngine:
    def generate(
        self,
        result: RuleResult,
    ) -> Comment | None:
        if result.status != RuleStatus.TRIGGERED:
            return None

        template = COMMENTS.get(result.rule_id)

        if template is None:
            return None

        return Comment(
            rule_id=result.rule_id,
            text=template.format(
                value=result.value,
            ),
        )
