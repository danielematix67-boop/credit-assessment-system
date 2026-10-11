from pathlib import Path

from src.config.rule_config_loader import RuleConfigLoader
from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.discovery import discover_rules

RULES_CONFIG_PATH = Path("config/financial_analysis_rules.yaml")


def test_financial_configuration_matches_discovered_rule_registry():
    configs = RuleConfigLoader().load(RULES_CONFIG_PATH)
    discover_rules()

    configured_rule_ids = [config.rule_id for config in configs]

    assert configured_rule_ids
    assert len(configured_rule_ids) == len(set(configured_rule_ids))
    assert set(configured_rule_ids) <= set(Rule._registry)


def test_financial_configuration_rules_are_instantiable_and_evaluable():
    configs = RuleConfigLoader().load(RULES_CONFIG_PATH)
    discover_rules()
    position = CreditPosition(
        position_id="integration-test",
        revenue_growth=0.05,
        revenue=1100.0,
        revenue_1y_ago=1000.0,
        trade_receivables_current=550.0,
        trade_receivables_1y_ago=500.0,
        ebitda=100.0,
        ebitda_margin=0.10,
        nfp_to_ebitda=4.0,
        tax_debt=50.0,
        total_liabilities=1000.0,
        intangible_assets=100.0,
        total_assets=2000.0,
        interest_expense=50.0,
        change_in_finished_goods_inventory=20.0,
        contribution_margin=400.0,
        net_operating_margin=100.0,
        operating_grants=150.0,
        production_value=1000.0,
        bank_debt_current=120.0,
        bank_debt_1y_ago=100.0,
        bank_debt_2y_ago=90.0,
        bank_debt_3y_ago=80.0,
        bank_debt_4y_ago=70.0,
        trade_payables_current=110.0,
        trade_payables_1y_ago=100.0,
        trade_payables_2y_ago=90.0,
        trade_payables_3y_ago=80.0,
        trade_payables_4y_ago=70.0,
        avg_payment_days_current=45.0,
        avg_payment_days_1y_ago=40.0,
        avg_payment_days_2y_ago=35.0,
        avg_payment_days_3y_ago=30.0,
        avg_payment_days_4y_ago=25.0,
        avg_collection_days_current=50.0,
        avg_collection_days_1y_ago=45.0,
        avg_collection_days_2y_ago=40.0,
        avg_collection_days_3y_ago=35.0,
        avg_collection_days_4y_ago=30.0,
    )

    results = []
    for config in configs:
        rule_class = Rule.get_registered_rule(config.rule_id)
        rule = rule_class(config)
        results.append(rule.evaluate(position))

    configured_rule_ids = [config.rule_id for config in configs]
    assert [result.rule_id for result in results] == configured_rule_ids
    assert all(result.status != RuleStatus.NOT_EVALUABLE for result in results)
    assert all(result.value is not None for result in results)


def test_financial_configuration_uses_supported_calculation_methods():
    configs = RuleConfigLoader().load(RULES_CONFIG_PATH)

    supported_calculations = {"direct", "ratio"}
    assert all(
        config.calculation in supported_calculations
        for config in configs
    )
