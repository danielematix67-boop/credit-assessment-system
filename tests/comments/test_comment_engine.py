import pytest

from src.comments.comment_engine import CommentEngine
from src.comments.templates import COMMENTS
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def comment_engine():
    return CommentEngine()


@pytest.fixture
def supported_rule_ids():
    """
    Return all rule IDs for which a comment template exists.
    """
    assert COMMENTS, "No comment templates are configured."

    return tuple(COMMENTS)


# ============================================================
# Helpers
# ============================================================


def make_rule_result(
    *,
    rule_id,
    status=RuleStatus.TRIGGERED,
    value=1.0,
    threshold=0.0,
    rule_name="Test rule",
    category="test",
    severity=RuleSeverity.MEDIUM,
):
    return RuleResult(
        rule_id=rule_id,
        rule_name=rule_name,
        category=category,
        status=status,
        value=value,
        threshold=threshold,
        severity=severity,
    )


def get_unsupported_rule_id():
    """
    Return an ID that is guaranteed not to have a configured
    comment template.
    """
    rule_id = "__UNSUPPORTED_RULE__"

    while rule_id in COMMENTS:
        rule_id = f"_{rule_id}_"

    return rule_id


# ============================================================
# Contract
# ============================================================


@pytest.mark.parametrize(
    "rule_id",
    tuple(COMMENTS),
)
def test_comment_engine_generates_comment_for_supported_rule(
    comment_engine,
    rule_id,
):
    result = make_rule_result(
        rule_id=rule_id,
    )

    comment = comment_engine.generate(result)

    assert comment is not None
    assert comment.rule_id == result.rule_id
    assert comment.text


def test_comment_engine_returns_none_for_unsupported_rule(
    comment_engine,
):
    result = make_rule_result(
        rule_id=get_unsupported_rule_id(),
    )

    comment = comment_engine.generate(result)

    assert comment is None


# ============================================================
# Rule status
# ============================================================


@pytest.mark.parametrize(
    "status",
    tuple(RuleStatus),
)
def test_comment_engine_only_generates_comments_for_triggered_results(
    comment_engine,
    supported_rule_ids,
    status,
):
    rule_id = supported_rule_ids[0]

    result = make_rule_result(
        rule_id=rule_id,
        status=status,
    )

    comment = comment_engine.generate(result)

    if status == RuleStatus.TRIGGERED:
        assert comment is not None
        assert comment.rule_id == result.rule_id
        assert comment.text
    else:
        assert comment is None


# ============================================================
# Template coverage
# ============================================================


def test_comment_engine_supports_all_configured_templates(
    comment_engine,
    supported_rule_ids,
):
    for rule_id in supported_rule_ids:
        result = make_rule_result(
            rule_id=rule_id,
        )

        comment = comment_engine.generate(result)

        assert comment is not None
        assert comment.rule_id == rule_id
        assert comment.text


# ============================================================
# Template rendering
# ============================================================


@pytest.mark.parametrize(
    "rule_id, template",
    tuple(COMMENTS.items()),
)
def test_comment_engine_renders_configured_template(
    comment_engine,
    rule_id,
    template,
):
    value = 123.456

    result = make_rule_result(
        rule_id=rule_id,
        value=value,
    )

    comment = comment_engine.generate(result)

    assert comment is not None

    expected_text = template.format(
        value=value,
    )

    assert comment.text == expected_text


# ============================================================
# RuleResult preservation
# ============================================================


@pytest.mark.parametrize(
    "rule_id",
    tuple(COMMENTS),
)
def test_comment_engine_does_not_modify_rule_result(
    comment_engine,
    rule_id,
):
    result = make_rule_result(
        rule_id=rule_id,
        value=123.0,
        threshold=100.0,
        rule_name="Arbitrary rule",
        category="arbitrary_category",
        severity=RuleSeverity.HIGH,
    )

    original_values = (
        result.rule_id,
        result.rule_name,
        result.category,
        result.status,
        result.value,
        result.threshold,
        result.severity,
    )

    original_result = result

    comment_engine.generate(result)

    assert result is original_result

    assert (
        result.rule_id,
        result.rule_name,
        result.category,
        result.status,
        result.value,
        result.threshold,
        result.severity,
    ) == original_values


# ============================================================
# Metadata independence
# ============================================================


@pytest.mark.parametrize(
    "rule_id",
    tuple(COMMENTS),
)
def test_comment_engine_uses_rule_id_as_template_key(
    comment_engine,
    rule_id,
):
    result = make_rule_result(
        rule_id=rule_id,
        rule_name="Arbitrary rule name",
        category="arbitrary_category",
        severity=RuleSeverity.HIGH,
    )

    comment = comment_engine.generate(result)

    assert comment is not None
    assert comment.rule_id == rule_id
    assert comment.text


# ============================================================
# Missing template handling
# ============================================================


def test_comment_engine_handles_missing_template_gracefully(
    comment_engine,
):
    unsupported_rule_id = get_unsupported_rule_id()

    result = make_rule_result(
        rule_id=unsupported_rule_id,
        status=RuleStatus.TRIGGERED,
    )

    assert result.rule_id not in COMMENTS

    assert comment_engine.generate(result) is None