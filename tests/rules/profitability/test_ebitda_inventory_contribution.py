from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.profitability.ebitda_inventory_contribution import (
    EbitdaInventoryContributionRule,
)


def create_rule() -> EbitdaInventoryContributionRule:
    config = RuleConfig(
        rule_id="R006",
        rule_name=(
            "EBITDA materially supported by finished goods "
            "inventory increase"
        ),
        category="profitability_quality",
        threshold=0.30,
        severity=RuleSeverity.MEDIUM,
    )

    return EbitdaInventoryContributionRule(config)


def test_ebitda_inventory_contribution_is_triggered():

    position = CreditPosition(
        position_id="POS001",
        ebitda=1_000_000,
        change_in_finished_goods_inventory=300_000,
    )

    rule = create_rule()

    result = rule.evaluate(position)

    assert result.rule_id == "R006"
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == 0.30
    assert result.threshold == 0.30


def test_ebitda_inventory_contribution_is_triggered_above_threshold():

    position = CreditPosition(
        position_id="POS001",
        ebitda=1_000_000,
        change_in_finished_goods_inventory=500_000,
    )

    rule = create_rule()

    result = rule.evaluate(position)

    assert result.status == RuleStatus.TRIGGERED
    assert result.value == 0.50


def test_ebitda_inventory_contribution_is_not_triggered_below_threshold():

    position = CreditPosition(
        position_id="POS001",
        ebitda=1_000_000,
        change_in_finished_goods_inventory=100_000,
    )

    rule = create_rule()

    result = rule.evaluate(position)

    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 0.10


def test_ebitda_inventory_contribution_is_not_triggered_for_negative_inventory_change():

    position = CreditPosition(
        position_id="POS001",
        ebitda=1_000_000,
        change_in_finished_goods_inventory=-100_000,
    )

    rule = create_rule()

    result = rule.evaluate(position)

    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == -0.10


def test_ebitda_inventory_contribution_is_not_evaluable_without_ebitda():

    position = CreditPosition(
        position_id="POS001",
        ebitda=None,
        change_in_finished_goods_inventory=300_000,
    )

    rule = create_rule()

    result = rule.evaluate(position)

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None


def test_ebitda_inventory_contribution_is_not_evaluable_without_inventory_change():

    position = CreditPosition(
        position_id="POS001",
        ebitda=1_000_000,
        change_in_finished_goods_inventory=None,
    )

    rule = create_rule()

    result = rule.evaluate(position)

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None


def test_ebitda_inventory_contribution_is_not_evaluable_with_negative_ebitda():

    position = CreditPosition(
        position_id="POS001",
        ebitda=-100_000,
        change_in_finished_goods_inventory=50_000,
    )

    rule = create_rule()

    result = rule.evaluate(position)

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
