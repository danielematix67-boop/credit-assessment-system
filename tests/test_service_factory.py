from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus
from src.services.service_factory import create_default_assessment_service


def test_default_assessment_service():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    service = create_default_assessment_service()

    assessment = service.assess(position)

    assert assessment.position_id == "POS001"

    # Five default rules are evaluated.
    assert len(assessment.rule_results) == 5

    # R001 - Revenue deterioration
    assert assessment.rule_results[0].rule_id == "R001"
    assert assessment.rule_results[0].status == RuleStatus.TRIGGERED

    # R002 - Negative EBITDA
    assert assessment.rule_results[1].rule_id == "R002"
    assert assessment.rule_results[1].status == RuleStatus.TRIGGERED

    # R003 - EBITDA margin deterioration
    assert assessment.rule_results[2].rule_id == "R003"
    assert assessment.rule_results[2].status == RuleStatus.TRIGGERED

    # R004 - PFN / EBITDA leverage
    assert assessment.rule_results[3].rule_id == "R004"
    assert assessment.rule_results[3].status == RuleStatus.TRIGGERED

    # R005 - Interest expense to EBITDA
    # Cannot be evaluated because EBITDA is negative.
    assert assessment.rule_results[4].rule_id == "R005"
    assert assessment.rule_results[4].status == RuleStatus.NOT_EVALUABLE

    # Only the four triggered rules generate comments.
    assert len(assessment.comments) == 4

    assert [comment.rule_id for comment in assessment.comments] == [
        "R001",
        "R002",
        "R003",
        "R004",
    ]


def test_default_assessment_service_with_healthy_position():
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    service = create_default_assessment_service()

    assessment = service.assess(position)

    assert assessment.position_id == "POS002"

    assert len(assessment.rule_results) == 5
    assert len(assessment.comments) == 0
