import pytest
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.profitability.financial_expenses_to_ebitda import (
    FinancialExpensesToEbitdaRule,
)
from src.rules.revenue.revenue_growth import RevenueGrowthRule
from src.rules.registry import build_rules, get_default_rules


def test_default_rules_registry():
    rules = get_default_rules()

    assert len(rules) == 5

    expected = [
        (
            RevenueGrowthRule,
            "R001",
            "Revenue growth deterioration",
            "revenue",
            -0.10,
            RuleSeverity.MEDIUM,
        ),
        (
            NegativeEbitdaRule,
            "R002",
            "Negative EBITDA",
            "profitability",
            0.0,
            RuleSeverity.HIGH,
        ),
        (
            EbitdaMarginRule,
            "R003",
            "EBITDA margin deterioration",
            "profitability",
            0.0,
            RuleSeverity.MEDIUM,
        ),
        (
            PfnToEbitdaRule,
            "R004",
            "PFN / EBITDA leverage",
            "leverage",
            5.0,
            RuleSeverity.HIGH,
        ),
        (
            FinancialExpensesToEbitdaRule,
            "R005",
            "Interest expense to EBITDA",
            "profitability",
            0.60,
            RuleSeverity.MEDIUM,
        ),
    ]

    for rule, (
        expected_type,
        expected_id,
        expected_name,
        expected_category,
        expected_threshold,
        expected_severity,
    ) in zip(rules, expected):
        assert isinstance(rule, expected_type)
        assert rule.config.rule_id == expected_id
        assert rule.config.rule_name == expected_name
        assert rule.config.category == expected_category
        assert rule.config.threshold == expected_threshold
        assert rule.config.severity == expected_severity


def test_default_rules_registry_preserves_yaml_order():
    rules = get_default_rules()

    assert [rule.config.rule_id for rule in rules] == [
        "R001",
        "R002",
        "R003",
        "R004",
        "R005",
    ]


def test_default_rules_registry_returns_independent_rule_instances():
    rules_1 = get_default_rules()
    rules_2 = get_default_rules()

    assert rules_1 is not rules_2

    for rule_1, rule_2 in zip(rules_1, rules_2):
        assert rule_1 is not rule_2
        assert rule_1.config is not rule_2.config


def test_build_rules_creates_correct_rule_types():
    configs = [
        RuleConfig(
            rule_id="R001",
            rule_name="Revenue growth deterioration",
            category="revenue",
            threshold=-0.10,
            severity=RuleSeverity.MEDIUM,
        ),
        RuleConfig(
            rule_id="R002",
            rule_name="Negative EBITDA",
            category="profitability",
            threshold=0.0,
            severity=RuleSeverity.HIGH,
        ),
        RuleConfig(
            rule_id="R003",
            rule_name="EBITDA margin deterioration",
            category="profitability",
            threshold=0.0,
            severity=RuleSeverity.MEDIUM,
        ),
        RuleConfig(
            rule_id="R004",
            rule_name="PFN / EBITDA leverage",
            category="leverage",
            threshold=5.0,
            severity=RuleSeverity.HIGH,
        ),
        RuleConfig(
            rule_id="R005",
            rule_name="Interest expense to EBITDA",
            category="profitability",
            threshold=0.60,
            severity=RuleSeverity.MEDIUM,
        ),
    ]

    rules = build_rules(configs)

    assert len(rules) == 5

    assert isinstance(rules[0], RevenueGrowthRule)
    assert isinstance(rules[1], NegativeEbitdaRule)
    assert isinstance(rules[2], EbitdaMarginRule)
    assert isinstance(rules[3], PfnToEbitdaRule)
    assert isinstance(rules[4], FinancialExpensesToEbitdaRule)


def test_build_rules_preserves_configuration_order():
    configs = [
        RuleConfig(
            rule_id="R004",
            rule_name="PFN / EBITDA leverage",
            category="leverage",
            threshold=5.0,
            severity=RuleSeverity.HIGH,
        ),
        RuleConfig(
            rule_id="R001",
            rule_name="Revenue growth deterioration",
            category="revenue",
            threshold=-0.10,
            severity=RuleSeverity.MEDIUM,
        ),
        RuleConfig(
            rule_id="R002",
            rule_name="Negative EBITDA",
            category="profitability",
            threshold=0.0,
            severity=RuleSeverity.HIGH,
        ),
    ]

    rules = build_rules(configs)

    assert [rule.config.rule_id for rule in rules] == [
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
    assert isinstance(rules[0], PfnToEbitdaRule)

    assert rules[0].config is config

def test_build_rules_raises_for_unknown_rule_id():
    config = RuleConfig(
        rule_id="R999",
        rule_name="Unknown rule",
        category="test",
        threshold=0.0,
        severity=RuleSeverity.LOW,
    )

    with pytest.raises(ValueError, match="Unknown rule_id: R999"):
        build_rules([config])