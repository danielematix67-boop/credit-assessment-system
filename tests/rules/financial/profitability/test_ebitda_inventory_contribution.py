import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.financial.profitability.ebitda_inventory_contribution import (
    EbitdaInventoryContributionRule,
)


RULE_ID = "TEST_RULE"
THRESHOLD = 0.30


@pytest.fixture
def rule_config():
    return RuleConfig(
        rule_id=RULE_ID,
        rule_name="Test EBITDA inventory contribution rule",
        category="test",
        threshold=THRESHOLD,
        severity=RuleSeverity.MEDIUM,
    )


@pytest.fixture
def rule(rule_config):
    return EbitdaInventoryContributionRule(rule_config)


@pytest.fixture
def ebitda():
    return 1_000_000


def make_position(
    *,
    ebitda: float | None,
    inventory_change: float | None,
) -> CreditPosition:
    return CreditPosition(
        position_id="TEST_POSITION",
        ebitda=ebitda,
        change_in_finished_goods_inventory=inventory_change,
    )


@pytest.mark.parametrize(
    ("inventory_change", "expected_value"),
    [
        (300_000, THRESHOLD),
        (500_000, 0.50),
    ],
)
def test_ebitda_inventory_contribution_is_triggered(
    rule,
    ebitda,
    inventory_change,
    expected_value,
):
    position = make_position(
        ebitda=ebitda,
        inventory_change=inventory_change,
    )

    result = rule.evaluate(position)

    assert result.rule_id == RULE_ID
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == expected_value
    assert result.threshold == THRESHOLD


@pytest.mark.parametrize(
    ("inventory_change", "expected_value"),
    [
        (100_000, 0.10),
        (-100_000, -0.10),
    ],
)
def test_ebitda_inventory_contribution_is_not_triggered(
    rule,
    ebitda,
    inventory_change,
    expected_value,
):
    position = make_position(
        ebitda=ebitda,
        inventory_change=inventory_change,
    )

    result = rule.evaluate(position)

    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == expected_value
    assert result.threshold == THRESHOLD


@pytest.mark.parametrize(
    ("ebitda", "inventory_change"),
    [
        (None, 300_000),
        (1_000_000, None),
        (-100_000, 50_000),
    ],
)
def test_ebitda_inventory_contribution_is_not_evaluable(
    rule,
    ebitda,
    inventory_change,
):
    position = make_position(
        ebitda=ebitda,
        inventory_change=inventory_change,
    )

    result = rule.evaluate(position)

    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.threshold == THRESHOLD