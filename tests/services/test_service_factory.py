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

    # The service must produce one result for every configured rule.
    assert len(assessment.rule_results) == len(
        service.rule_engine.rules
    )

    results = {
        result.rule_id: result
        for result in assessment.rule_results
    }

    findings = {
        finding.result.rule_id: finding
        for finding in assessment.findings
    }

    configured_rule_ids = {
        rule.config.rule_id
        for rule in service.rule_engine.rules
    }

    assert set(results) == configured_rule_ids

    triggered_rules = {
        result.rule_id
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    }

    assert len(triggered_rules) >= 2

    # Only triggered rules with a configured comment
    # generate findings.
    assert set(findings).issubset(triggered_rules)

    # Every finding must contain the corresponding
    # rule result and its associated comment.
    for finding in assessment.findings:
        assert finding.result.status == RuleStatus.TRIGGERED
        assert finding.comment.rule_id == finding.result.rule_id
        assert finding.comment.text


def test_default_assessment_service_generates_comments_for_triggered_rules():

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

    triggered_results = {
        result.rule_id: result
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    }

    findings = {
        finding.result.rule_id: finding
        for finding in assessment.findings
    }

    for rule_id, result in triggered_results.items():

        finding = findings.get(rule_id)

        if finding is not None:
            assert finding.result is result
            assert finding.comment.rule_id == rule_id
            assert finding.comment.text


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

    assert len(assessment.rule_results) == len(
        service.rule_engine.rules
    )

    results = {
        result.rule_id: result
        for result in assessment.rule_results
    }

    configured_rule_ids = {
        rule.config.rule_id
        for rule in service.rule_engine.rules
    }

    assert set(results) == configured_rule_ids

    assert all(
        result.status != RuleStatus.TRIGGERED
        for result in assessment.rule_results
    )

    assert assessment.findings == []