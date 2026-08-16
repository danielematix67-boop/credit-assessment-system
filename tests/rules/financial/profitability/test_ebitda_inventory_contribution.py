import pytest

from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_threshold import SeverityThreshold
from src.rules.base.status import RuleStatus
from src.rules.financial.profitability.ebitda_inventory_contribution import (
    EbitdaInventoryContributionRule,
)


RULE_ID = "TEST_RULE"
RULE_NAME = "Test EBITDA inventory contribution rule"
CATEGORY = "test"
THRESHOLD = 0.30
DEFAULT_SEVERITY = RuleSeverity.LOW


@pytest.fixture
def rule_config():
    return RuleConfig(
        rule_id=RULE_ID,
        rule_name=RULE_NAME,
        category=CATEGORY,
        threshold=THRESHOLD,
        severity=DEFAULT_SEVERITY,
        severity_thresholds=(
            SeverityThreshold(
                threshold=0.30,
                severity=RuleSeverity.MEDIUM,
            ),
            SeverityThreshold(
                threshold=0.50,
                severity=RuleSeverity.HIGH,
            ),
        ),
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


def assert_result_metadata(result, config):
    assert result.rule_id == config.rule_id
    assert result.rule_name == config.rule_name
    assert result.category == config.category
    assert result.threshold == config.threshold


@pytest.mark.parametrize(
    (
        "inventory_change",
        "expected_value",
        "expected_status",
        "expected_severity",
    ),
    [
        (
            100_000,
            0.10,
            RuleStatus.NOT_TRIGGERED,
            RuleSeverity.LOW,
        ),
        (
            300_000,
            0.30,
            RuleStatus.TRIGGERED,
            RuleSeverity.MEDIUM,
        ),
        (
            400_000,
            0.40,
            RuleStatus.TRIGGERED,
            RuleSeverity.MEDIUM,
        ),
        (
            500_000,
            0.50,
            RuleStatus.TRIGGERED,
            RuleSeverity.HIGH,
        ),
        (
            600_000,
            0.60,
            RuleStatus.TRIGGERED,
            RuleSeverity.HIGH,
        ),
    ],
)
def test_ebitda_inventory_contribution_evaluates_ratio(
    rule,
    rule_config,
    ebitda,
    inventory_change,
    expected_value,
    expected_status,
    expected_severity,
):
    position = make_position(
        ebitda=ebitda,
        inventory_change=inventory_change,
    )

    result = rule.evaluate(position)

    assert_result_metadata(result, rule_config)
    assert result.value == expected_value
    assert result.status == expected_status
    assert result.severity == expected_severity


def test_ebitda_inventory_contribution_threshold_is_inclusive(
    rule,
    ebitda,
):
    position = make_position(
        ebitda=ebitda,
        inventory_change=300_000,
    )

    result = rule.evaluate(position)

    assert result.value == THRESHOLD
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity == RuleSeverity.MEDIUM


@pytest.mark.parametrize(
    ("inventory_change", "expected_value"),
    [
        (-100_000, -0.10),
        (0, 0.00),
    ],
)
def test_ebitda_inventory_contribution_below_threshold_is_not_triggered(
    rule,
    rule_config,
    ebitda,
    inventory_change,
    expected_value,
):
    position = make_position(
        ebitda=ebitda,
        inventory_change=inventory_change,
    )

    result = rule.evaluate(position)

    assert_result_metadata(result, rule_config)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == expected_value
    assert result.severity == RuleSeverity.LOW


@pytest.mark.parametrize(
    ("ebitda", "inventory_change"),
    [
        (None, 300_000),
        (1_000_000, None),
        (-100_000, 50_000),
        (0, 50_000),
    ],
)
def test_ebitda_inventory_contribution_is_not_evaluable(
    rule,
    rule_config,
    ebitda,
    inventory_change,
):
    position = make_position(
        ebitda=ebitda,
        inventory_change=inventory_change,
    )

    result = rule.evaluate(position)

    assert_result_metadata(result, rule_config)
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.severity == rule_config.severity