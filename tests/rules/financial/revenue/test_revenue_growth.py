from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.status import RuleStatus
from src.rules.base.severity import RuleSeverity
from src.rules.financial.revenue.revenue_growth import RevenueGrowthRule


R001_CONFIG = RuleConfig(
    rule_id="R001",
    rule_name="Revenue deterioration",
    category="revenue",
    threshold=-0.10,
    severity=RuleSeverity.MEDIUM,
)


def test_revenue_growth_rule_triggered():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=250000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = RevenueGrowthRule(R001_CONFIG)
    result = rule.evaluate(position)

    assert result.rule_id == "R001"
    assert result.rule_name == "Revenue deterioration"
    assert result.category == "revenue"
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == -0.15
    assert result.threshold == -0.10
    assert result.severity == RuleSeverity.MEDIUM


def test_revenue_growth_rule_not_triggered():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = RevenueGrowthRule(R001_CONFIG)
    result = rule.evaluate(position)

    assert result.rule_id == "R001"
    assert result.rule_name == "Revenue deterioration"
    assert result.category == "revenue"
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == 0.05
    assert result.threshold == -0.10
    assert result.severity == RuleSeverity.MEDIUM


def test_revenue_growth_rule_not_evaluable_when_none():
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=None,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = RevenueGrowthRule(R001_CONFIG)
    result = rule.evaluate(position)

    assert result.rule_id == "R001"
    assert result.rule_name == "Revenue deterioration"
    assert result.category == "revenue"
    assert result.status == RuleStatus.NOT_EVALUABLE
    assert result.value is None
    assert result.threshold == -0.10
    assert result.severity == RuleSeverity.MEDIUM


def test_revenue_growth_rule_uses_configured_threshold():
    config = RuleConfig(
        rule_id="R001_CUSTOM",
        rule_name="Custom revenue deterioration",
        category="revenue",
        threshold=-0.20,
        severity=RuleSeverity.HIGH,
    )

    position = CreditPosition(
        position_id="POS004",
        revenue_growth=-0.15,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule = RevenueGrowthRule(config)
    result = rule.evaluate(position)

    assert result.rule_id == "R001_CUSTOM"
    assert result.rule_name == "Custom revenue deterioration"
    assert result.category == "revenue"
    assert result.status == RuleStatus.NOT_TRIGGERED
    assert result.value == -0.15
    assert result.threshold == -0.20
    assert result.severity == RuleSeverity.HIGH