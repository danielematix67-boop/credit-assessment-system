from src.models.assessment_status import AssessmentStatus
from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus
from src.services.service_factory import create_default_assessment_service


def test_default_assessment_service_generates_critical_assessment():
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
    assert assessment.status == AssessmentStatus.CRITICAL

    assert len(assessment.rule_results) == 6
    assert len(assessment.comments) == 4

    results = {
        result.rule_id: result
        for result in assessment.rule_results
    }

    comments = {
        comment.rule_id: comment
        for comment in assessment.comments
    }

    # R001 - Revenue growth deterioration
    assert results["R001"].status == RuleStatus.TRIGGERED

    # R002 - Negative EBITDA
    assert results["R002"].status == RuleStatus.TRIGGERED

    # R003 - EBITDA margin deterioration
    assert results["R003"].status == RuleStatus.TRIGGERED

    # R004 - PFN / EBITDA leverage
    assert results["R004"].status == RuleStatus.TRIGGERED

    # R005 - Interest expense to EBITDA
    # Cannot be evaluated because EBITDA is negative.
    assert results["R005"].status == RuleStatus.NOT_EVALUABLE
    assert results["R005"].value is None

    # R006 - EBITDA materially supported by finished goods
    # inventory increase.
    # Cannot be evaluated because the inventory variation
    # is not provided.
    assert results["R006"].status == RuleStatus.NOT_EVALUABLE
    assert results["R006"].value is None

    # Only triggered rules generate comments.
    assert set(comments.keys()) == {
        "R001",
        "R002",
        "R003",
        "R004",
    }


def test_default_assessment_service_generates_normal_assessment():
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
    assert assessment.status == AssessmentStatus.NORMAL

    assert len(assessment.rule_results) == 6
    assert len(assessment.comments) == 0

    results = {
        result.rule_id: result
        for result in assessment.rule_results
    }

    # Existing rules are not triggered.
    assert all(
        result.status == RuleStatus.NOT_TRIGGERED
        for rule_id, result in results.items()
        if rule_id != "R006"
    )

    # R006 cannot be evaluated because the finished goods
    # inventory variation is not provided.
    assert results["R006"].status == RuleStatus.NOT_EVALUABLE
    assert results["R006"].value is None
