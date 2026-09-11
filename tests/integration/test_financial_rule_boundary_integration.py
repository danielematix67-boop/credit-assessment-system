from pathlib import Path

import pytest

from src.config.rule_config_loader import RuleConfigLoader
from src.models.position import CreditPosition
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.discovery import discover_rules

RULES_CONFIG_PATH = Path("config/financial_analysis_rules.yaml")


@pytest.fixture(scope="module")
def financial_rules():
    discover_rules()
    configs = RuleConfigLoader().load(RULES_CONFIG_PATH)
    return {config.rule_id: Rule.get_registered_rule(config.rule_id)(config) for config in configs}


def test_ratio_rules_calculate_configured_values(financial_rules):
    position = CreditPosition(
        position_id="ratio-integration-test",
        ebitda=100.0,
        interest_expense=50.0,
        change_in_finished_goods_inventory=20.0,
    )

    assert financial_rules["R005"].evaluate(position).value == pytest.approx(0.50)
    assert financial_rules["R006"].evaluate(position).value == pytest.approx(0.20)
    assert financial_rules["R007"].evaluate(position).value == pytest.approx(2.00)


def test_ratio_rules_apply_configured_trigger_boundaries(financial_rules):
    position = CreditPosition(
        position_id="boundary-integration-test",
        ebitda=100.0,
        interest_expense=50.0,
        change_in_finished_goods_inventory=30.0,
    )

    assert financial_rules["R005"].evaluate(position).status == RuleStatus.NOT_TRIGGERED
    assert financial_rules["R006"].evaluate(position).status == RuleStatus.NOT_TRIGGERED
    assert financial_rules["R007"].evaluate(position).status == RuleStatus.NOT_TRIGGERED

    position.interest_expense = 70.0
    position.change_in_finished_goods_inventory = 40.0
    position.ebitda = 100.0

    assert financial_rules["R005"].evaluate(position).status == RuleStatus.TRIGGERED
    assert financial_rules["R006"].evaluate(position).status == RuleStatus.TRIGGERED
    assert financial_rules["R007"].evaluate(position).status == RuleStatus.TRIGGERED


def test_ratio_rules_resolve_severity_independently_at_boundaries(financial_rules):
    position = CreditPosition(
        position_id="severity-boundary-integration-test",
        ebitda=100.0,
        interest_expense=50.0,
        change_in_finished_goods_inventory=30.0,
    )

    r005 = financial_rules["R005"].evaluate(position)
    r006 = financial_rules["R006"].evaluate(position)
    r007 = financial_rules["R007"].evaluate(position)

    assert r005.severity.name == "LOW"
    assert r006.severity.name == "MEDIUM"
    assert r007.severity.name == "MEDIUM"

    position.interest_expense = 100.0
    position.change_in_finished_goods_inventory = 50.0
    position.ebitda = 100.0

    r005 = financial_rules["R005"].evaluate(position)
    r006 = financial_rules["R006"].evaluate(position)
    r007 = financial_rules["R007"].evaluate(position)

    assert r005.severity.name == "HIGH"
    assert r006.severity.name == "HIGH"
    assert r007.severity.name == "HIGH"
