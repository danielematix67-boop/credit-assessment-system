import pytest

from src.models.assessment_status import AssessmentStatus
from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus
from src.services.service_factory import create_default_assessment_service


@pytest.fixture
def assessment_service():
    return create_default_assessment_service()


@pytest.fixture
def critical_position():
    return CreditPosition(
        position_id="CRITICAL_POSITION",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )


@pytest.fixture
def normal_position():
    return CreditPosition(
        position_id="NORMAL_POSITION",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )


def test_default_assessment_service_produces_complete_assessment(
    assessment_service,
    critical_position,
):
    assessment = assessment_service.assess(critical_position)

    assert assessment.position_id == critical_position.position_id
    assert assessment.status == AssessmentStatus.CRITICAL

    configured_rule_ids = {
        rule.config.rule_id
        for rule in assessment_service.rule_engine.rules
    }

    result_ids = {
        result.rule_id
        for result in assessment.rule_results
    }

    assert result_ids == configured_rule_ids


def test_default_assessment_service_produces_findings_consistent_with_triggered_rules(
    assessment_service,
    critical_position,
):
    assessment = assessment_service.assess(critical_position)

    triggered_results = {
        result.rule_id: result
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    }

    findings = {
        finding.result.rule_id: finding
        for finding in assessment.findings
    }

    assert set(findings).issubset(triggered_results)

    for rule_id, finding in findings.items():
        result = triggered_results[rule_id]

        assert finding.result is result
        assert finding.comment.rule_id == rule_id
        assert finding.comment.text


def test_default_assessment_service_generates_expected_status_for_normal_position(
    assessment_service,
    normal_position,
):
    assessment = assessment_service.assess(normal_position)

    assert assessment.position_id == normal_position.position_id
    assert assessment.status == AssessmentStatus.NORMAL

    configured_rule_ids = {
        rule.config.rule_id
        for rule in assessment_service.rule_engine.rules
    }

    result_ids = {
        result.rule_id
        for result in assessment.rule_results
    }

    assert result_ids == configured_rule_ids

    assert all(
        result.status != RuleStatus.TRIGGERED
        for result in assessment.rule_results
    )

    assert assessment.findings == []