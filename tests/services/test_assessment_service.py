from src.models.assessment_status import AssessmentStatus
from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus


def test_assessment_service_generates_critical_assessment(assessment_service):
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    assessment = assessment_service.assess(position)

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

    # Rule statuses
    assert results["R001"].status == RuleStatus.TRIGGERED
    assert results["R002"].status == RuleStatus.TRIGGERED
    assert results["R003"].status == RuleStatus.TRIGGERED
    assert results["R004"].status == RuleStatus.TRIGGERED
    assert results["R005"].status == RuleStatus.NOT_EVALUABLE

    # R006 - EBITDA materially supported by finished goods
    # inventory increase.
    # Cannot be evaluated because inventory variation is missing.
    assert results["R006"].status == RuleStatus.NOT_EVALUABLE
    assert results["R006"].value is None

    # Generated comments
    assert comments["R001"].text == (
        "Revenue deterioration detected. "
        "Revenue growth: -15.0% (threshold: -10.0%)."
    )

    assert comments["R002"].text == (
        "Negative EBITDA detected. "
        "EBITDA: €-50,000 (threshold: €0)."
    )

    assert comments["R003"].text == (
        "EBITDA margin is below the acceptable threshold. "
        "EBITDA margin: -5.0% (threshold: 0.0%)."
    )

    assert comments["R004"].text == (
        "Leverage is above the acceptable threshold. "
        "PFN to EBITDA: 6.0x (threshold: 5.0x)."
    )


def test_assessment_service_generates_normal_assessment_when_rule_is_not_evaluable(
    assessment_service,
):
    position = CreditPosition(
        position_id="POS002",
        revenue_growth=None,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    assessment = assessment_service.assess(position)

    assert assessment.position_id == "POS002"
    assert assessment.status == AssessmentStatus.NORMAL

    assert len(assessment.rule_results) == 6
    assert len(assessment.comments) == 0

    results = {
        result.rule_id: result
        for result in assessment.rule_results
    }

    # R001 cannot be evaluated because revenue growth is missing.
    assert results["R001"].status == RuleStatus.NOT_EVALUABLE
    assert results["R001"].value is None

    # R006 cannot be evaluated because finished goods inventory
    # variation is missing.
    assert results["R006"].status == RuleStatus.NOT_EVALUABLE
    assert results["R006"].value is None

    # All other rules are evaluable and not triggered.
    assert all(
        result.status == RuleStatus.NOT_TRIGGERED
        for result in assessment.rule_results
        if result.rule_id not in {"R001", "R006"}
    )


def test_assessment_service_generates_normal_assessment(assessment_service):
    position = CreditPosition(
        position_id="POS003",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    assessment = assessment_service.assess(position)

    assert assessment.position_id == "POS003"
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
        for result in assessment.rule_results
        if result.rule_id != "R006"
    )

    # R006 cannot be evaluated because finished goods inventory
    # variation is missing.
    assert results["R006"].status == RuleStatus.NOT_EVALUABLE
    assert results["R006"].value is None


def test_assessment_service_generates_attention_assessment(assessment_service):
    position = CreditPosition(
        position_id="POS004",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    assessment = assessment_service.assess(position)

    assert assessment.position_id == "POS004"
    assert assessment.status == AssessmentStatus.ATTENTION

    assert len(assessment.rule_results) == 6
    assert len(assessment.comments) == 1

    results = {
        result.rule_id: result
        for result in assessment.rule_results
    }

    comments = {
        comment.rule_id: comment
        for comment in assessment.comments
    }

    # R006 cannot be evaluated because finished goods inventory
    # variation is missing.
    assert results["R006"].status == RuleStatus.NOT_EVALUABLE
    assert results["R006"].value is None

    assert comments["R004"].text == (
        "Leverage is above the acceptable threshold. "
        "PFN to EBITDA: 6.0x (threshold: 5.0x)."
    )
