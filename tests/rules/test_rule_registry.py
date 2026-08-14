import pytest

from src.rules.base.config import RuleConfig
from src.rules.base.rule import Rule
from src.rules.base.severity import RuleSeverity
from src.rules.registry import build_rules, get_default_rules

def test_rule_registry_rejects_unknown_rule_id():

    with pytest.raises(
        ValueError,
        match="Unknown rule_id: UNKNOWN_RULE",
    ):
        Rule.get_registered_rule("UNKNOWN_RULE")


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

    for rule_1, rule_2 in zip(rules_1, rules_2):
        assert rule_1 is not rule_2
        assert rule_1.config is not rule_2.config


def test_build_rules_creates_rules_from_configuration():
    configs = [
        RuleConfig(
            rule_id="R001",
            rule_name="Rule one",
            category="test",
            threshold=0.0,
            severity=RuleSeverity.MEDIUM,
        ),
        RuleConfig(
            rule_id="R002",
            rule_name="Rule two",
            category="test",
            threshold=1.0,
            severity=RuleSeverity.HIGH,
        ),
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


def test_build_rules_preserves_configuration_order():
    configs = [
        RuleConfig(
            rule_id="R004",
            rule_name="Rule four",
            category="test",
            threshold=4.0,
            severity=RuleSeverity.HIGH,
        ),
        RuleConfig(
            rule_id="R001",
            rule_name="Rule one",
            category="test",
            threshold=1.0,
            severity=RuleSeverity.MEDIUM,
        ),
        RuleConfig(
            rule_id="R002",
            rule_name="Rule two",
            category="test",
            threshold=2.0,
            severity=RuleSeverity.LOW,
        ),
    ]

    rules = build_rules(configs)

    assert [
        rule.config.rule_id
        for rule in rules
    ] == [
        "R004",
        "R001",
        "R002",
    ]


def test_build_rules_preserves_configuration_object():
    config = RuleConfig(
        rule_id="R004",
        rule_name="PFN / EBITDA leverage",
        category="leverage",
        threshold=4.5,
        severity=RuleSeverity.HIGH,
    )

    rules = build_rules([config])

    assert len(rules) == 1
    assert isinstance(rules[0], Rule)

    assert rules[0].config is config


def test_build_rules_raises_for_unknown_rule_id():
    config = RuleConfig(
        rule_id="R999",
        rule_name="Unknown rule",
        category="test",
        threshold=0.0,
        severity=RuleSeverity.LOW,
    )

    with pytest.raises(
        ValueError,
        match="Unknown rule_id: R999",
    ):
        build_rules([config])


def test_build_rules_maps_registered_rule_ids():
    rules = get_default_rules()

    for rule in rules:
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


def test_build_rules_uses_configuration_threshold():
    config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.20,
        severity=RuleSeverity.MEDIUM,
    )

    rules = build_rules([config])

    assert len(rules) == 1
    assert isinstance(rules[0], Rule)

    assert rules[0].config.rule_id == "R001"
    assert rules[0].config.threshold == -0.20
    assert rules[0].config.severity == RuleSeverity.MEDIUM
