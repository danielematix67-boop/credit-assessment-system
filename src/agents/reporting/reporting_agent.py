from src.agents.base.agent import Agent
from src.models.assessment import Assessment
from src.models.assessment_status import AssessmentStatus
from src.models.report import Report
from src.rules.base.status import RuleStatus


class ReportingAgent(Agent[Assessment, Report]):

    def run(self, assessment: Assessment) -> Report:
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

        findings = [
            result.rule_name
            for result in triggered_rules
        ]

        limitations = [
            result.rule_name
            for result in not_evaluable_rules
        ]

        if assessment.status == AssessmentStatus.NORMAL:
            summary = (
                "The credit assessment is classified as normal."
            )
        elif assessment.status == AssessmentStatus.ATTENTION:
            summary = (
                "The credit assessment requires attention."
            )
        elif assessment.status == AssessmentStatus.CRITICAL:
            summary = (
                "The credit assessment is classified as critical."
            )
        else:
            summary = (
                "The credit assessment has an undefined status."
            )

        return Report(
            position_id=assessment.position_id,
            assessment_status=assessment.status,
            executive_summary=summary,
            findings=findings,
            limitations=limitations,
        )
