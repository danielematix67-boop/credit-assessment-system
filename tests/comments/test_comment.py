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
def supported_rule_id():
    """
    Return one configured rule ID.

    The test suite does not depend on a specific rule ID.
    """
    assert COMMENTS, "No comment templates are configured."

    return next(iter(COMMENTS))


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


def make_unsupported_rule_id():
    """
    Generate an ID that is guaranteed not to be configured.
    """
    candidate = "__UNSUPPORTED_RULE__"

    while candidate in COMMENTS:
        candidate = f"_{candidate}_"

    return candidate


# ============================================================
# Generation contract
# ============================================================


def test_generates_comment_for_configured_rule(
    comment_engine,
    supported_rule_id,
):
    result = make_rule_result(
        rule_id=supported_rule_id,
    )

    comment = comment_engine.generate(result)

    assert comment is not None
    assert comment.rule_id == result.rule_id
    assert comment.text


def test_returns_none_for_unconfigured_rule(
    comment_engine,
):
    result = make_rule_result(
        rule_id=make_unsupported_rule_id(),
    )

    assert comment_engine.generate(result) is None


# ============================================================
# Status contract
# ============================================================


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


# ============================================================
# Configuration coverage
# ============================================================


@pytest.mark.parametrize(
    "rule_id",
    tuple(COMMENTS),
)
def test_all_configured_rules_have_usable_templates(
    comment_engine,
    rule_id,
):
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
def test_configured_template_is_rendered(
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
# Input immutability
# ============================================================


@pytest.mark.parametrize(
    "rule_id",
    tuple(COMMENTS),
)
def test_does_not_modify_rule_result(
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

    original_state = (
        result.rule_id,
        result.rule_name,
        result.category,
        result.status,
        result.value,
        result.threshold,
        result.severity,
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
    ) == original_state


# ============================================================
# Metadata independence
# ============================================================


@pytest.mark.parametrize(
    "rule_id",
    tuple(COMMENTS),
)
def test_generation_depends_on_rule_id_not_metadata(
    comment_engine,
    rule_id,
):
    result = make_rule_result(
        rule_id=rule_id,
        rule_name="Arbitrary name",
        category="arbitrary category",
        severity=RuleSeverity.HIGH,
    )

    comment = comment_engine.generate(result)

    assert comment is not None
    assert comment.rule_id == rule_id
    assert comment.text


# ============================================================
# Severity independence
# ============================================================


@pytest.mark.parametrize(
    "severity",
    tuple(RuleSeverity),
)
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
