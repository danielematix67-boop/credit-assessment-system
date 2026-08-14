from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.sustainability.leverage.pfn_to_ebitda import PfnToEbitdaRule


R004_CONFIG = RuleConfig(
    rule_id="R004",
    rule_name="PFN / EBITDA leverage",
    category="leverage",
    threshold=5.0,
    severity=RuleSeverity.HIGH,
)


def create_rule(
    config: RuleConfig = R004_CONFIG,
) -> PfnToEbitdaRule:
    return PfnToEbitdaRule(config)


def assert_result_matches_config(
    result,
    config: RuleConfig,
) -> None:
    assert result.rule_id == config.rule_id
    assert result.rule_name == config.rule_name
    assert result.category == config.category
    assert result.threshold == config.threshold
    assert result.severity == config.severity


def test_pfn_to_ebitda_rule_triggered():
    pfn_to_ebitda = 6.0

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=pfn_to_ebitda,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == pfn_to_ebitda


def test_pfn_to_ebitda_rule_not_triggered():
    pfn_to_ebitda = 3.5

    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=pfn_to_ebitda,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == pfn_to_ebitda


def test_pfn_to_ebitda_rule_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=None,
        interest_expense=40_000,
    )

    result = create_rule().evaluate(position)

    assert_result_matches_config(result, R004_CONFIG)
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None


def test_pfn_to_ebitda_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id=f"{R004_CONFIG.rule_id}_CUSTOM",
        rule_name="Custom PFN / EBITDA threshold",
        category=R004_CONFIG.category,
        threshold=7.0,
        severity=RuleSeverity.MEDIUM,
    )

    pfn_to_ebitda = 6.0

    position = CreditPosition(
        position_id="POS004",
        revenue_growth=0.05,
        ebitda=250_000,
        profit_loss=50_000,
        ebitda_margin=0.10,
        pfn_to_ebitda=pfn_to_ebitda,
        interest_expense=40_000,
    )

    result = create_rule(config).evaluate(position)

    assert_result_matches_config(result, config)
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == pfn_to_ebitda