from src.config.rule_configuration import RuleConfiguration
from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.registry import build_rules, get_default_rules
from src.rules.revenue.revenue_growth import RevenueGrowthRule


def test_rule_engine_evaluates_all_configured_rules():
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

    # The engine must return exactly one result for every configured rule.
    assert len(results) == len(rules)

    # Every configured rule must produce exactly one result.
    assert {
        result.rule_id
        for result in results
    } == {
        rule.config.rule_id
        for rule in rules
    }


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
            rule_id="R003",
            rule_name="EBITDA margin deterioration",
            category="profitability",
            threshold=0.0,
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

    engine = RuleEngine(rules)

    results = engine.evaluate(position)

    assert [result.rule_id for result in results] == [
        config.rule_id
        for config in configs
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

    # Find the rule affected by the missing revenue growth
    # without relying on its position in the result list.
    revenue_growth_result = next(
        result
        for result in results
        if result.rule_id == "R001"
    )

    assert revenue_growth_result.status == RuleStatus.NOT_EVALUABLE
    assert revenue_growth_result.value is None
    assert revenue_growth_result.threshold == -0.10


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
