from unittest.mock import MagicMock

from src.comments.comment import Comment
from src.comments.comment_engine import CommentEngine
from src.engine.finding_engine import FindingEngine
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


def test_finding_engine_generates_rule_finding_from_comment():

    result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.HIGH,
    )

    comment = Comment(
        rule_id="R001",
        text="Revenue deterioration detected.",
    )

    comment_engine = MagicMock(spec=CommentEngine)
    comment_engine.generate.return_value = comment

    engine = FindingEngine(comment_engine)

    finding = engine.generate(result)

    assert isinstance(finding, RuleFinding)
    assert finding.result is result
    assert finding.comment is comment

    comment_engine.generate.assert_called_once_with(result)


def test_finding_engine_returns_none_when_comment_is_not_available():

    result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="Financial",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.HIGH,
    )

    comment_engine = MagicMock(spec=CommentEngine)
    comment_engine.generate.return_value = None

    engine = FindingEngine(comment_engine)

    finding = engine.generate(result)

    assert finding is None

    comment_engine.generate.assert_called_once_with(result)