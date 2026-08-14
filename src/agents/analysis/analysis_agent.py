from src.agents.base.agent import Agent
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus


class AnalysisAgent(Agent[Assessment, AssessmentAnalysis]):

    def run(
        self,
        assessment: Assessment,
    ) -> AssessmentAnalysis:

        triggered_findings = [
            finding
            for finding in assessment.findings
            if finding.result.status == RuleStatus.TRIGGERED
        ]

        not_evaluable_findings = [
            finding
            for finding in assessment.findings
            if finding.result.status == RuleStatus.NOT_EVALUABLE
        ]

        key_findings = [
            finding.comment.text
            for finding in triggered_findings
        ]

        risk_factors = [
            finding.comment.text
            for finding in triggered_findings
            if finding.result.severity == RuleSeverity.HIGH
        ]

        limitations = [
            finding.comment.text
            for finding in not_evaluable_findings
        ]

        return AssessmentAnalysis(
            position_id=assessment.position_id,
            assessment_status=assessment.status,
            key_findings=key_findings,
            risk_factors=risk_factors,
            limitations=limitations,
        )