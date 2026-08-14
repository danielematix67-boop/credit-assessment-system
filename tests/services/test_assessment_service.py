from unittest.mock import MagicMock

from src.models.assessment import Assessment
from src.models.assessment_status import AssessmentStatus
from src.models.position import CreditPosition
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.assessment_service import AssessmentService


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

    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    triggered_rules = {
        result.rule_id
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    }

    finding_rule_ids = {
        finding.result.rule_id
        for finding in assessment.findings
    }

    assert finding_rule_ids == triggered_rules
    assert len(assessment.findings) == len(triggered_rules)


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

    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    assert all(
        result.status != RuleStatus.TRIGGERED
        for result in assessment.rule_results
    )

    assert assessment.findings == []


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

    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    assert all(
        result.status != RuleStatus.TRIGGERED
        for result in assessment.rule_results
    )

    assert assessment.findings == []


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

    assert len(assessment.rule_results) == len(
        assessment_service.rule_engine.rules
    )

    triggered_rules = {
        result.rule_id
        for result in assessment.rule_results
        if result.status == RuleStatus.TRIGGERED
    }

    finding_rule_ids = {
        finding.result.rule_id
        for finding in assessment.findings
    }

    assert finding_rule_ids == triggered_rules
    assert len(assessment.findings) == len(triggered_rules)


def test_assessment_service_builds_assessment_from_dependencies():
    position = CreditPosition(
        position_id="POS005",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule_engine = MagicMock()
    comment_engine = MagicMock()
    status_calculator = MagicMock()

    result = RuleResult(
        rule_id="R001",
        rule_name="Revenue Growth",
        category="revenue",
        status=RuleStatus.TRIGGERED,
        value=-0.15,
        threshold=-0.10,
        severity=RuleSeverity.MEDIUM,
    )

    rule_engine.evaluate.return_value = [result]

    comment = MagicMock()
    comment_engine.generate.return_value = comment

    status_calculator.calculate.return_value = AssessmentStatus.CRITICAL

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
    assert assessment.status == AssessmentStatus.CRITICAL

    rule_engine.evaluate.assert_called_once_with(position)
    comment_engine.generate.assert_called_once_with(result)
    status_calculator.calculate.assert_called_once_with([result])


def test_assessment_service_ignores_missing_comments():
    position = CreditPosition(
        position_id="POS006",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=50000,
        ebitda_margin=0.10,
        pfn_to_ebitda=3.5,
        interest_expense=40000,
    )

    rule_engine = MagicMock()
    comment_engine = MagicMock()
    status_calculator = MagicMock()

    result_1 = MagicMock()
    result_2 = MagicMock()

    rule_engine.evaluate.return_value = [
        result_1,
        result_2,
    ]

    comment_1 = MagicMock()

    comment_engine.generate.side_effect = [
        comment_1,
        None,
    ]

    status_calculator.calculate.return_value = AssessmentStatus.ATTENTION

    service = AssessmentService(
        rule_engine=rule_engine,
        comment_engine=comment_engine,
        status_calculator=status_calculator,
    )

    assessment = service.assess(position)

    assert len(assessment.findings) == 1
    assert assessment.findings[0].result == result_1
    assert assessment.findings[0].comment == comment_1

    assert comment_engine.generate.call_count == 2