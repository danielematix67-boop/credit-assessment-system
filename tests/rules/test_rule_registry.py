import pytest

from src.rules.base.config import RuleConfig
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.registry import build_rules, get_default_rules


@pytest.fixture
def rule_config():
    return RuleConfig(
        rule_id="TEST_RULE",
        rule_name="Test rule",
        category="test",
        threshold=1.0,
        severity=RuleSeverity.MEDIUM,
    )


@pytest.fixture
def registered_rule_id():
    rules = get_default_rules()

    assert rules

    return rules[0].config.rule_id


def test_rule_registry_rejects_unknown_rule_id():
    unknown_rule_id = "UNKNOWN_RULE"

    with pytest.raises(
        ValueError,
        match=f"Unknown rule_id: {unknown_rule_id}",
    ):
        Rule.get_registered_rule(unknown_rule_id)


def test_default_rules_registry_returns_rules():
    rules = get_default_rules()

    assert rules
    assert all(
        isinstance(rule, Rule)
        for rule in rules
    )


def test_default_rules_registry_returns_unique_rule_ids():
    rules = get_default_rules()

    rule_ids = [
        rule.config.rule_id
        for rule in rules
    ]

    assert len(rule_ids) == len(set(rule_ids))


def test_default_rules_registry_returns_independent_rule_instances():
    rules_1 = get_default_rules()
    rules_2 = get_default_rules()

    assert rules_1 is not rules_2
    assert len(rules_1) == len(rules_2)

    for rule_1, rule_2 in zip(rules_1, rules_2):
        assert rule_1 is not rule_2
        assert rule_1.config is not rule_2.config


def test_build_rules_creates_rules_from_configuration():
    configs = [
        RuleConfig(
            rule_id=rule.config.rule_id,
            rule_name="Test rule",
            category="test",
            threshold=float(index),
            severity=RuleSeverity.MEDIUM,
        )
        for index, rule in enumerate(get_default_rules())
    ]

    rules = build_rules(configs)

    assert len(rules) == len(configs)

    assert all(
        isinstance(rule, Rule)
        for rule in rules
    )

    assert [
        rule.config.rule_id
        for rule in rules
    ] == [
        config.rule_id
        for config in configs
    ]


def test_build_rules_preserves_configuration_order(
    registered_rule_id,
):
    available_rules = get_default_rules()

    rule_ids = [
        rule.config.rule_id
        for rule in available_rules
    ]

    if len(rule_ids) < 2:
        pytest.skip("At least two registered rules are required.")

    ordered_ids = list(reversed(rule_ids))

    configs = [
        RuleConfig(
            rule_id=rule_id,
            rule_name="Test rule",
            category="test",
            threshold=float(index),
            severity=RuleSeverity.MEDIUM,
        )
        for index, rule_id in enumerate(ordered_ids)
    ]

    rules = build_rules(configs)

    assert [
        rule.config.rule_id
        for rule in rules
    ] == ordered_ids


def test_build_rules_preserves_configuration_object(
    registered_rule_id,
):
    config = RuleConfig(
        rule_id=registered_rule_id,
        rule_name="Test rule",
        category="test",
        threshold=1.0,
        severity=RuleSeverity.MEDIUM,
    )

    rules = build_rules([config])

    assert len(rules) == 1
    assert isinstance(rules[0], Rule)
    assert rules[0].config is config


def test_build_rules_raises_for_unknown_rule_id():
    unknown_rule_id = "UNKNOWN_RULE"

    config = RuleConfig(
        rule_id=unknown_rule_id,
        rule_name="Unknown rule",
        category="test",
        threshold=0.0,
        severity=RuleSeverity.LOW,
    )

    with pytest.raises(
        ValueError,
        match=f"Unknown rule_id: {unknown_rule_id}",
    ):
        build_rules([config])


def test_build_rules_maps_registered_rule_ids():
    for rule in get_default_rules():
        config = RuleConfig(
            rule_id=rule.config.rule_id,
            rule_name="Test rule",
            category="test",
            threshold=0.0,
            severity=RuleSeverity.MEDIUM,
        )

        built_rules = build_rules([config])

        assert len(built_rules) == 1
        assert isinstance(built_rules[0], Rule)
        assert built_rules[0].config.rule_id == rule.config.rule_id


def test_build_rules_uses_configuration_values(
    registered_rule_id,
):
    threshold = 123.45
    severity = RuleSeverity.HIGH

    config = RuleConfig(
        rule_id=registered_rule_id,
        rule_name="Test rule",
        category="test",
        threshold=threshold,
        severity=severity,
    )

    rules = build_rules([config])

    assert len(rules) == 1
    assert rules[0].config is config
    assert rules[0].config.threshold == threshold
    assert rules[0].config.severity == severity