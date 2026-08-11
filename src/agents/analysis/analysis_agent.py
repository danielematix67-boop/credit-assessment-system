from src.agents.base.agent import Agent
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.rules.base.status import RuleStatus


class AnalysisAgent(Agent[Assessment, AssessmentAnalysis]):

    def run(
        self,
        assessment: Assessment,
    ) -> AssessmentAnalysis:

        triggered_rules = [
            result
            for result in assessment.rule_results
            if result.status == RuleStatus.TRIGGERED
        ]

        not_evaluable_rules = [
            result
            for result in assessment.rule_results
            if result.status == RuleStatus.NOT_EVALUABLE
        ]

        key_findings = [
            result.rule_name
            for result in triggered_rules
        ]

        risk_factors = [
            result.rule_name
            for result in triggered_rules
        ]

        limitations = [
            result.rule_name
            for result in not_evaluable_rules
        ]

        return AssessmentAnalysis(
            position_id=assessment.position_id,
            assessment_status=assessment.status,
            key_findings=key_findings,
            risk_factors=risk_factors,
            limitations=limitations,
        )