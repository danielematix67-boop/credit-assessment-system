import pytest

from src.comments.comment import Comment
from src.comments.comment_engine import CommentEngine
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@pytest.fixture
def comment_engine() -> CommentEngine:
    return CommentEngine()


@pytest.fixture
def supported_rule_id() -> str:
    return "TEST_RULE"


def make_rule_result(
    *,
    rule_id: str,
    status: RuleStatus = RuleStatus.TRIGGERED,
    value: float = 1.0,
    threshold: float = 0.0,
    rule_name: str = "Test rule",
    category: str = "test",
    severity: RuleSeverity = RuleSeverity.MEDIUM,
    comment_template: str = "Value is {value}.",
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        status=status,
        value=value,
        threshold=threshold,
        severity=severity,
        comment_template=comment_template,
    )


def test_generates_comment_for_configured_rule(comment_engine, supported_rule_id):
    result = make_rule_result(rule_id=supported_rule_id)

    comment = comment_engine.generate(result)

    assert isinstance(comment, Comment)
    assert comment.rule_id == result.rule_id
    assert comment.text == "Value is 1.0."


def test_returns_none_for_unconfigured_comment_template(comment_engine):
    result = make_rule_result(rule_id="UNCONFIGURED", comment_template="")

    assert comment_engine.generate(result) is None


@pytest.mark.parametrize("status", tuple(RuleStatus))
def test_generates_comments_only_for_triggered_results(
    comment_engine,
    supported_rule_id,
    status,
):
    result = make_rule_result(
        rule_id=supported_rule_id,
        status=status,
    )

    comment = comment_engine.generate(result)

    if status == RuleStatus.TRIGGERED:
        assert comment is not None
        assert comment.rule_id == result.rule_id
        assert comment.text
    else:
        assert comment is None


def test_configured_template_is_rendered(comment_engine):
    result = make_rule_result(
        rule_id="R001",
        value=123.456,
        comment_template="Indicator is {value:.2f}.",
    )

    comment = comment_engine.generate(result)

    assert comment is not None
    assert comment.text == "Indicator is 123.46."


def test_does_not_modify_rule_result(comment_engine):
    result = make_rule_result(
        rule_id="R001",
        value=123.0,
        threshold=100.0,
        rule_name="Arbitrary rule",
        category="arbitrary_category",
        severity=RuleSeverity.HIGH,
    )

    original_state = (
        result.rule_id,
        result.rule_name,
        result.category,
        result.status,
        result.value,
        result.threshold,
        result.severity,
        result.comment_template,
    )
    original_object = result

    comment_engine.generate(result)

    assert result is original_object
    assert (
        result.rule_id,
        result.rule_name,
        result.category,
        result.status,
        result.value,
        result.threshold,
        result.severity,
        result.comment_template,
    ) == original_state


def test_generation_depends_on_rule_result_configuration_not_metadata(comment_engine):
    result = make_rule_result(
        rule_id="R001",
        rule_name="Arbitrary name",
        category="arbitrary category",
        severity=RuleSeverity.HIGH,
        comment_template="Configured comment for {value}.",
    )

    comment = comment_engine.generate(result)

    assert comment is not None
    assert comment.rule_id == result.rule_id
    assert comment.text == "Configured comment for 1.0."


@pytest.mark.parametrize("severity", tuple(RuleSeverity))
def test_generation_is_independent_of_severity(
    comment_engine,
    supported_rule_id,
    severity,
):
    result = make_rule_result(
        rule_id=supported_rule_id,
        severity=severity,
    )

    comment = comment_engine.generate(result)

    assert comment is not None
    assert comment.rule_id == result.rule_id
    assert comment.text
