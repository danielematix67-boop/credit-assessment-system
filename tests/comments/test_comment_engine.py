from pathlib import Path

import pytest

from src.comments.comment_engine import CommentEngine
from src.config.rule_config_loader import RuleConfigLoader
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult

CONFIG_PATHS = (
    Path("config/customer_profile_rules.yaml"),
    Path("config/financial_analysis_rules.yaml"),
    Path("config/behavioural_analysis_rules.yaml"),
    Path("config/debt_sustainability_rules.yaml"),
)


@pytest.fixture
def comment_engine():
    return CommentEngine()


@pytest.fixture
def configured_rules():
    loader = RuleConfigLoader()
    return [config for path in CONFIG_PATHS for config in loader.load(path)]


def make_rule_result(
    *,
    rule_id: str = "TEST_RULE",
    comment_template: str = "Configured comment for value {value:.1f}.",
    status: RuleStatus = RuleStatus.TRIGGERED,
    value: float | None = 123.456,
    threshold: float = 0.0,
    rule_name: str = "Test rule",
    category: str = "test",
    severity: RuleSeverity = RuleSeverity.MEDIUM,
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


def test_comment_engine_generates_comment_from_rule_result_template(comment_engine):
    result = make_rule_result(
        comment_template="Revenue growth is {value:.1%}.",
        value=-0.125,
    )

    comment = comment_engine.generate(result)

    assert comment is not None
    assert comment.rule_id == result.rule_id
    assert comment.text == "Revenue growth is -12.5%."


@pytest.mark.parametrize("status", list(RuleStatus))
def test_comment_engine_only_generates_comments_for_triggered_results(
    comment_engine,
    status,
):
    result = make_rule_result(status=status)
    comment = comment_engine.generate(result)

    if status == RuleStatus.TRIGGERED:
        assert comment is not None
    else:
        assert comment is None


def test_all_configured_rules_have_deterministic_comment_templates(configured_rules):
    assert configured_rules
    for config in configured_rules:
        assert config.comment_template, f"Missing comment_template for {config.rule_id}"


def test_comment_engine_renders_all_configured_rule_templates(comment_engine, configured_rules):
    for config in configured_rules:
        result = make_rule_result(
            rule_id=config.rule_id,
            comment_template=config.comment_template,
            value=123.456,
            threshold=config.threshold,
            rule_name=config.rule_name,
            category=config.category,
            severity=config.severity,
        )
        comment = comment_engine.generate(result)
        assert comment is not None
        assert comment.rule_id == config.rule_id
        assert comment.text == config.comment_template.format(value=123.456)


def test_comment_engine_uses_changed_yaml_comment_template_without_python_lookup(
    comment_engine,
    tmp_path,
):
    config_path = tmp_path / "rules.yaml"
    config_path.write_text(
        """
rules:
  - rule_id: TEST_RULE
    rule_name: Test rule
    category: test
    threshold: 1.0
    severity: MEDIUM
    severity_direction: HIGHER_IS_WORSE
    input_field: test_value
    comment_template: 'YAML policy text: {value:.2f}.'
""",
        encoding="utf-8",
    )

    config = RuleConfigLoader().load(config_path)[0]
    result = make_rule_result(
        rule_id=config.rule_id,
        comment_template=config.comment_template,
        value=42.0,
    )

    comment = comment_engine.generate(result)

    assert comment is not None
    assert comment.text == "YAML policy text: 42.00."


def test_comment_engine_returns_none_when_configured_template_is_missing(comment_engine):
    result = make_rule_result(comment_template="")
    assert comment_engine.generate(result) is None


def test_comment_engine_does_not_use_rule_id_as_a_second_template_source(comment_engine):
    result = make_rule_result(
        rule_id="R001",
        comment_template="Authoritative configured text: {value:.0f}.",
        value=42.0,
    )
    comment = comment_engine.generate(result)
    assert comment is not None
    assert comment.text == "Authoritative configured text: 42."


def test_comment_engine_does_not_modify_rule_result(comment_engine):
    result = make_rule_result(
        rule_id="R001",
        value=123.0,
        threshold=100.0,
        rule_name="Arbitrary rule",
        category="arbitrary_category",
        severity=RuleSeverity.HIGH,
    )
    original = result
    comment_engine.generate(result)
    assert result is original
    assert result.comment_template == "Configured comment for value {value:.1f}."
