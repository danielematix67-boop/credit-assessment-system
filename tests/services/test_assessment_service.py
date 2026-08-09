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

    # The assessment must contain one result for every configured rule.
    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    results = {
        result.rule_id: result
        for result in assessment.rule_results
    }

    comments = {
        comment.rule_id: comment
        for comment in assessment.comments
    }

    # Critical assessment must contain the expected triggered rules.
    expected_triggered_rules = {
        "R001",
        "R002",
        "R003",
        "R004",
    }

    assert {
        result.rule_id
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    } == expected_triggered_rules

    # R005 is not evaluable because EBITDA is negative.
    assert results["R005"].status == RuleStatus.NOT_EVALUABLE
    assert results["R005"].value is None

    # Only triggered rules generate comments.
    assert set(comments) == expected_triggered_rules

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

    # The assessment must contain one result for every configured rule.
    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    # No triggered rule means no comments.
    assert assessment.comments == []

    results = {
        result.rule_id: result
        for result in assessment.rule_results
    }

    # R001 cannot be evaluated because revenue growth is missing.
    assert results["R001"].status == RuleStatus.NOT_EVALUABLE
    assert results["R001"].value is None

    # A NORMAL assessment means that no rule was triggered.
    # Other rules may be NOT_EVALUABLE when input data is missing.
    assert all(
        result.status != RuleStatus.TRIGGERED
        for result in assessment.rule_results
    )


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

    # The assessment must contain one result for every configured rule.
    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    # No triggered rule means no comments.
    assert assessment.comments == []

    # A NORMAL assessment means that no rule was triggered.
    # Individual rules may still be NOT_EVALUABLE.
    assert all(
        result.status != RuleStatus.TRIGGERED
        for result in assessment.rule_results
    )


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

    # The assessment must contain one result for every configured rule.
    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    comments = {
        comment.rule_id: comment
        for comment in assessment.comments
    }

    # Only R004 is triggered in this scenario.
    assert {
        result.rule_id
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    } == {"R004"}

    assert set(comments) == {"R004"}

    assert comments["R004"].text == (
        "Leverage is above the acceptable threshold. "
        "PFN to EBITDA: 6.0x (threshold: 5.0x)."
    )
