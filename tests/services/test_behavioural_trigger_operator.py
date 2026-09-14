import pytest

from src.models.behavioural_data import BehaviouralData
from src.models.position import CreditPosition
from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.status import RuleStatus
from src.rules.behavioural.b001 import HighCreditUtilizationRule
from src.services.behavioural_assessment_service import BehaviouralAssessmentService


@pytest.mark.parametrize(
    ("operator", "value", "expected"),
    [
        ("GT", 1.1, True),
        ("GT", 1.0, False),
        ("GTE", 1.0, True),
        ("GTE", 0.9, False),
        ("LT", 0.9, True),
        ("LT", 1.0, False),
        ("LTE", 1.0, True),
        ("LTE", 1.1, False),
    ],
)
def test_behavioural_trigger_operator_semantics(
    operator: str,
    value: float,
    expected: bool,
) -> None:
    rule = HighCreditUtilizationRule(
        RuleConfig(
            rule_id="B001",
            rule_name="Test behavioural rule",
            category="test",
            input_field="revenue",
            threshold=1.0,
            trigger_operator=operator,
            severity=RuleSeverity.MEDIUM,
            severity_direction=SeverityDirection.HIGHER_IS_WORSE,
        )
    )

    result = rule.evaluate(CreditPosition(position_id="TEST", revenue=value))

    assert result.status == (
        RuleStatus.TRIGGERED if expected else RuleStatus.NOT_TRIGGERED
    )


def test_behavioural_trigger_operator_rejects_unknown_operator() -> None:
    with pytest.raises(ValueError, match="trigger_operator must be one of"):
        RuleConfig(
            rule_id="B001",
            rule_name="Test behavioural rule",
            category="test",
            input_field="revenue",
            threshold=1.0,
            trigger_operator="INVALID",
            severity=RuleSeverity.MEDIUM,
            severity_direction=SeverityDirection.HIGHER_IS_WORSE,
        )


def test_behavioural_assessment_uses_configured_threshold_and_operator(tmp_path) -> None:
    config_path = tmp_path / "behavioural_rules.yaml"
    config_path.write_text(
        """
        rules:
          - rule_id: B001
            rule_name: Configured utilization rule
            indicator: Credit utilization
            category: utilization
            input_field: average_utilization
            threshold: 0.80
            trigger_operator: GTE
            severity: MEDIUM
            severity_direction: HIGHER_IS_WORSE
            severity_thresholds:
              - threshold: 0.80
                severity: MEDIUM
              - threshold: 0.95
                severity: HIGH
            comment_template: >-
              Configured utilization is {value:.1%}.
        """,
        encoding="utf-8",
    )

    section = BehaviouralAssessmentService(config_path=config_path).assess(
        BehaviouralData(average_utilization=0.80)
    )

    result = section.evidence[0]
    assert result.rule_id == "B001"
    assert result.status == RuleStatus.TRIGGERED
    assert result.threshold == pytest.approx(0.80)
    assert result.comment_template == "Configured utilization is {value:.1%}."
