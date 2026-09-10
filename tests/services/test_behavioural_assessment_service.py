from src.models.assessment_section import SectionStatus
from src.models.behavioural_data import BehaviouralData
from src.rules.base.status import RuleStatus
from src.services.behavioural_assessment_service import BehaviouralAssessmentService


def test_behavioural_assessment_is_normal_when_indicators_are_below_thresholds() -> None:
    section = BehaviouralAssessmentService().assess(
        BehaviouralData(
            average_utilization=0.60,
            overdraft_days=2,
            payment_delay_days=5,
            exposure_growth=0.10,
        )
    )

    assert section.status == SectionStatus.NORMAL
    assert all(result.status == RuleStatus.NOT_TRIGGERED for result in section.evidence)
    assert section.findings == []


def test_behavioural_assessment_triggers_high_utilization() -> None:
    section = BehaviouralAssessmentService().assess(
        BehaviouralData(average_utilization=0.97)
    )

    result = next(item for item in section.evidence if item.rule_id == "B001")
    assert result.status == RuleStatus.TRIGGERED
    assert result.severity.value == "HIGH"
    assert len(section.findings) == 1


def test_behavioural_assessment_triggers_multiple_risks() -> None:
    section = BehaviouralAssessmentService().assess(
        BehaviouralData(
            average_utilization=0.92,
            overdraft_days=15,
            payment_delay_days=0,
            exposure_growth=0.05,
        )
    )

    assert section.status == SectionStatus.CRITICAL
    assert [result.rule_id for result in section.evidence if result.is_triggered] == [
        "B001",
        "B002",
    ]


def test_behavioural_assessment_preserves_not_evaluable_data() -> None:
    section = BehaviouralAssessmentService().assess(BehaviouralData())

    assert section.status == SectionStatus.ATTENTION
    assert all(result.status == RuleStatus.NOT_EVALUABLE for result in section.evidence)
    assert len(section.evidence) == 4


def test_behavioural_assessment_uses_high_severity_thresholds() -> None:
    section = BehaviouralAssessmentService().assess(
        BehaviouralData(
            overdraft_days=31,
            payment_delay_days=61,
            exposure_growth=0.41,
        )
    )

    severities = {
        result.rule_id: result.severity.value
        for result in section.evidence
        if result.status == RuleStatus.TRIGGERED
    }
    assert severities == {"B002": "HIGH", "B003": "HIGH", "B004": "HIGH"}
