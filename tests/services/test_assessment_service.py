from src.models.assessment_status import AssessmentStatus
from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus


def test_assessment_service_generates_critical_assessment(
    assessment_service,
):
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

    # One result must be produced for every configured rule.
    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    triggered_rules = {
        result.rule_id
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    }

    comment_rule_ids = {
        comment.rule_id
        for comment in assessment.comments
    }

    # Every triggered rule must generate exactly one comment.
    assert comment_rule_ids == triggered_rules

    # Every comment must correspond to a triggered rule.
    assert len(assessment.comments) == len(triggered_rules)


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

    # One result must be produced for every configured rule.
    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    # A NORMAL assessment must not contain triggered rules.
    assert all(
        result.status != RuleStatus.TRIGGERED
        for result in assessment.rule_results
    )

    # No triggered rule means no comments.
    assert assessment.comments == []


def test_assessment_service_generates_normal_assessment(
    assessment_service,
):
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

    # One result must be produced for every configured rule.
    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    # A NORMAL assessment must not contain triggered rules.
    assert all(
        result.status != RuleStatus.TRIGGERED
        for result in assessment.rule_results
    )

    # No triggered rule means no comments.
    assert assessment.comments == []


def test_assessment_service_generates_attention_assessment(
    assessment_service,
):
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

    # One result must be produced for every configured rule.
    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    triggered_rules = {
        result.rule_id
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    }

    comment_rule_ids = {
        comment.rule_id
        for comment in assessment.comments
    }

    # Every triggered rule must generate exactly one comment.
    assert comment_rule_ids == triggered_rules

    # Every comment must correspond to a triggered rule.
    assert len(assessment.comments) == len(triggered_rules)
