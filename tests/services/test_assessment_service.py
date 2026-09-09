from unittest.mock import MagicMock

import pytest

from src.models.assessment import Assessment
from src.models.assessment_status import AssessmentStatus
from src.models.position import CreditPosition
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_service import AssessmentService


@pytest.fixture(
    params=[
        pytest.param(
            {
                "position_id": "CRITICAL_POSITION",
                "revenue_growth": -0.15,
                "ebitda": -50000,
                "profit_loss": -50000,
                "ebitda_margin": -0.05,
                "nfp_to_ebitda": 6.0,
                "interest_expense": 40000,
                "expected_status": AssessmentStatus.CRITICAL,
            },
            id="critical",
        ),
        pytest.param(
            {
                "position_id": "NORMAL_POSITION",
                "revenue_growth": 0.05,
                "ebitda": 250000,
                "profit_loss": 50000,
                "ebitda_margin": 0.10,
                "nfp_to_ebitda": 3.5,
                "interest_expense": 40000,
                "expected_status": AssessmentStatus.NORMAL,
            },
            id="normal",
        ),
        pytest.param(
            {
                "position_id": "ATTENTION_POSITION",
                "revenue_growth": 0.05,
                "ebitda": 250000,
                "profit_loss": 50000,
                "ebitda_margin": 0.10,
                "nfp_to_ebitda": 6.0,
                "interest_expense": 40000,
                "expected_status": AssessmentStatus.ATTENTION,
            },
            id="attention",
        ),
    ]
)
def assessment_scenario(request):
    return request.param


@pytest.fixture
def assessment_position(assessment_scenario):
    scenario = assessment_scenario.copy()

    scenario.pop("expected_status")

    return CreditPosition(**scenario)


def test_assessment_service_generates_expected_assessment(
    assessment_service,
    assessment_position,
    assessment_scenario,
):
    assessment = assessment_service.assess(assessment_position)

    assert isinstance(assessment, Assessment)
    assert assessment.position_id == assessment_position.position_id

    assert assessment.status == assessment_scenario["expected_status"]

    assert len(assessment.rule_results) == len(assessment_service.rule_engine.rules)


def test_assessment_service_creates_findings_for_triggered_rules(
    assessment_service,
    assessment_position,
):
    assessment = assessment_service.assess(assessment_position)

    triggered_rules = {
        result.rule_id
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    }

    finding_rule_ids = {finding.result.rule_id for finding in assessment.findings}

    assert finding_rule_ids == triggered_rules
    assert len(assessment.findings) == len(triggered_rules)


def test_assessment_service_does_not_create_findings_for_non_triggered_rules(
    assessment_service,
):
    position = CreditPosition(
        position_id="NON_EVALUABLE_POSITION",
        revenue_growth=None,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        nfp_to_ebitda=3.5,
        interest_expense=40000,
    )

    assessment = assessment_service.assess(position)

    assert all(
        result.status != RuleStatus.TRIGGERED for result in assessment.rule_results
    )

    assert assessment.findings == []


def test_assessment_service_builds_assessment_from_dependencies():
    position = CreditPosition(
        position_id="TEST_POSITION",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        nfp_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule_engine = MagicMock()
    comment_engine = MagicMock()
    status_calculator = MagicMock()

    result = RuleResult(
        rule_id="TEST_RULE",
        rule_name="Test rule",
        category="test",
        status=RuleStatus.TRIGGERED,
        value=1.0,
        threshold=0.0,
        severity=RuleSeverity.MEDIUM,
    )

    rule_engine.evaluate.return_value = [result]

    comment = MagicMock()
    comment_engine.generate.return_value = comment

    expected_status = AssessmentStatus.CRITICAL
    status_calculator.calculate.return_value = expected_status

    service = AssessmentService(
        rule_engine=rule_engine,
        comment_engine=comment_engine,
        status_calculator=status_calculator,
    )

    assessment = service.assess(position)

    expected_finding = RuleFinding(
        result=result,
        comment=comment,
    )

    assert isinstance(assessment, Assessment)
    assert assessment.position_id == position.position_id
    assert assessment.rule_results == [result]
    assert assessment.findings == [expected_finding]
    assert assessment.status == expected_status

    rule_engine.evaluate.assert_called_once_with(position)
    comment_engine.generate.assert_called_once_with(result)
    status_calculator.calculate.assert_called_once_with([result])


def test_assessment_service_skips_results_without_comments():
    position = CreditPosition(
        position_id="TEST_POSITION",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        nfp_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule_engine = MagicMock()
    comment_engine = MagicMock()
    status_calculator = MagicMock()

    result_with_comment = MagicMock()
    result_without_comment = MagicMock()

    rule_engine.evaluate.return_value = [
        result_with_comment,
        result_without_comment,
    ]

    comment = MagicMock()

    comment_engine.generate.side_effect = [
        comment,
        None,
    ]

    expected_status = AssessmentStatus.ATTENTION
    status_calculator.calculate.return_value = expected_status

    service = AssessmentService(
        rule_engine=rule_engine,
        comment_engine=comment_engine,
        status_calculator=status_calculator,
    )

    assessment = service.assess(position)

    assert assessment.findings == [
        RuleFinding(
            result=result_with_comment,
            comment=comment,
        )
    ]

    assert comment_engine.generate.call_count == 2
