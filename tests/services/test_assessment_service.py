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

    comments = {
        comment.rule_id: comment
        for comment in assessment.comments
    }

    # These are the rules expected to trigger in this
    # specific critical scenario.
    expected_triggered_rules = {
        "R001",
        "R002",
        "R003",
        "R004",
    }

    triggered_rules = {
        result.rule_id
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    }

    assert triggered_rules == expected_triggered_rules

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

    comments = {
        comment.rule_id: comment
        for comment in assessment.comments
    }

    # This scenario is expected to trigger only the leverage rule.
    expected_triggered_rules = {"R004"}

    triggered_rules = {
        result.rule_id
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    }

    assert triggered_rules == expected_triggered_rules

    # Only triggered rules generate comments.
    assert set(comments) == expected_triggered_rules

    assert comments["R004"].text == (
        "Leverage is above the acceptable threshold. "
        "PFN to EBITDA: 6.0x (threshold: 5.0x)."
    )
