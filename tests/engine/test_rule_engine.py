from pathlib import Path

from src.config.rule_configuration import RuleConfiguration
from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.leverage.pfn_to_ebitda import PfnToEbitdaRule
from src.rules.profitability.ebitda_inventory_contribution import (
    EbitdaInventoryContributionRule,
)
from src.rules.profitability.ebitda_margin import EbitdaMarginRule
from src.rules.profitability.negative_ebitda import NegativeEbitdaRule
from src.rules.revenue.revenue_growth import RevenueGrowthRule
from src.rules.registry import build_rules, get_default_rules


def test_rule_engine_evaluates_all_rules():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6,
        interest_expense=40000,
    )

    rules = get_default_rules()

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    assert len(results) == 6

    assert results[0].rule_id == "R001"
    assert results[0].status == RuleStatus.TRIGGERED

    assert results[1].rule_id == "R002"
    assert results[1].status == RuleStatus.TRIGGERED

    assert results[2].rule_id == "R003"
    assert results[2].status == RuleStatus.TRIGGERED

    assert results[3].rule_id == "R004"
    assert results[3].status == RuleStatus.TRIGGERED

    assert results[4].rule_id == "R005"
    assert results[4].status == RuleStatus.NOT_EVALUABLE

    # R006 - EBITDA materially supported by finished goods
    # inventory increase.
    # Cannot be evaluated because the inventory variation is missing.
    assert results[5].rule_id == "R006"
    assert results[5].status == RuleStatus.NOT_EVALUABLE
    assert results[5].value is None


def test_rule_engine_preserves_rule_order():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6,
        interest_expense=40000,
    )

    pfn_to_ebitda_config = RuleConfig(
        rule_id="R004",
        rule_name="PFN / EBITDA leverage",
        category="leverage",
        threshold=5.0,
        severity=RuleSeverity.HIGH,
    )

    revenue_growth_config = RuleConfig(
        rule_id="R001",
        rule_name="Revenue growth deterioration",
        category="revenue",
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    ebitda_margin_config = RuleConfig(
        rule_id="R003",
        rule_name="EBITDA margin deterioration",
        category="profitability",
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
    )

    negative_ebitda_config = RuleConfig(
        rule_id="R002",
        rule_name="Negative EBITDA",
        category="profitability",
        threshold=0.0,
        severity=RuleSeverity.HIGH,
    )

    rules = [
        PfnToEbitdaRule(pfn_to_ebitda_config),
        RevenueGrowthRule(revenue_growth_config),
        EbitdaMarginRule(ebitda_margin_config),
        NegativeEbitdaRule(negative_ebitda_config),
    ]

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    assert [result.rule_id for result in results] == [
        "R004",
        "R001",
        "R003",
        "R002",
    ]


def test_rule_engine_with_no_rules():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    engine = RuleEngine([])

    results = engine.evaluate(position)

    assert results == []


def test_rule_engine_preserves_not_evaluable_status():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=None,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rules = get_default_rules()

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    revenue_growth_result = results[0]

    assert revenue_growth_result.rule_id == "R001"
    assert revenue_growth_result.status == RuleStatus.NOT_EVALUABLE
    assert revenue_growth_result.value is None
    assert revenue_growth_result.threshold == -0.10

    # R006 is also not evaluable because the finished goods
    # inventory variation is missing.
    inventory_contribution_result = results[5]

    assert inventory_contribution_result.rule_id == "R006"
    assert inventory_contribution_result.status == RuleStatus.NOT_EVALUABLE
    assert inventory_contribution_result.value is None


def test_get_default_rules_uses_custom_configuration(tmp_path):
    config_path = tmp_path / "rules.yaml"

    config_path.write_text(
        """
        rules:
          - rule_id: R001
            rule_name: Custom revenue rule
            category: revenue
            threshold: -0.20
            severity: HIGH
        """,
        encoding="utf-8",
    )

    configuration = RuleConfiguration(config_path)

    rules = get_default_rules(configuration)

    assert len(rules) == 1
    assert isinstance(rules[0], RevenueGrowthRule)
    assert rules[0].config.rule_id == "R001"
    assert rules[0].config.rule_name == "Custom revenue rule"
    assert rules[0].config.threshold == -0.20
    assert rules[0].config.severity == RuleSeverity.HIGH


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
    assert isinstance(rules[0], RevenueGrowthRule)

    assert rules[0].config.rule_id == "R001"
    assert rules[0].config.threshold == -0.20
    assert rules[0].config.severity == RuleSeverity.MEDIUM
