from src.agents.base.agent import Agent
from src.models.assessment import Assessment
from src.models.report import Report


class ReportingAgent(Agent[Assessment, Report]):

    def run(self, assessment: Assessment) -> Report:
        triggered_rules = [
            result
            for result in assessment.rule_results
            if result.status.value == "TRIGGERED"
        ]

        findings = [
            result.rule_name
            for result in triggered_rules
        ]

        if assessment.status.value == "NORMAL":
            summary = (
                "The credit assessment is classified as normal."
            )
        elif assessment.status.value == "ATTENTION":
            summary = (
                "The credit assessment requires attention."
            )
        else:
            summary = (
                "The credit assessment is classified as critical."
            )

        return Report(
            position_id=assessment.position_id,
            assessment_status=assessment.status,
            executive_summary=summary,
            findings=findings,
            limitations=[],
        )