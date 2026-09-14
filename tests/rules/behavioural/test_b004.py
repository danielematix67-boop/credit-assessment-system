from types import SimpleNamespace

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.behavioural.b004 import ExposureGrowthRule


def make_rule() -> ExposureGrowthRule:
    return ExposureGrowthRule(
        RuleConfig(
            rule_id="B004",
            rule_name="Exposure Growth",
            category="exposure",
            threshold=0.25,
            severity=RuleSeverity.MEDIUM,
            severity_direction="HIGHER_IS_WORSE",
            input_field="exposure_growth",
            trigger_operator="GT",
        )
    )


def test_exposure_growth_above_threshold_triggers() -> None:
    assert make_rule().evaluate(SimpleNamespace(exposure_growth=0.30)).status.value == "TRIGGERED"


def test_exposure_growth_at_threshold_does_not_trigger() -> None:
    assert make_rule().evaluate(SimpleNamespace(exposure_growth=0.25)).status.value == "NOT_TRIGGERED"


def test_missing_exposure_growth_is_not_evaluable() -> None:
    assert make_rule().evaluate(SimpleNamespace(exposure_growth=None)).status.value == "NOT_EVALUABLE"
