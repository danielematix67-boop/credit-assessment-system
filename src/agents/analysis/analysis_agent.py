from src.agents.base.agent import Agent
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment import Assessment
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.rule_finding import RuleFinding
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


class AnalysisAgent(Agent[Assessment, AssessmentAnalysis]):
    """Adapt deterministic assessment evidence into the analysis contract.

    This agent only interprets deterministic evidence. It does not recalculate
    rule outcomes, thresholds, severities, or the final assessment status.
    """

    @staticmethod
    def _to_analysis_finding(
        finding: RuleFinding,
    ) -> AnalysisFinding:
        return AnalysisFinding(
            rule_id=finding.result.rule_id,
            category=finding.result.category,
            severity=finding.result.severity,
            text=finding.comment.text,
        )

    @staticmethod
    def _to_limitation(
        result: RuleResult,
    ) -> AnalysisFinding:
        return AnalysisFinding(
            rule_id=result.rule_id,
            category=result.category,
            severity=result.severity,
            text=(
                result.reason
                if result.reason is not None
                else f"{result.rule_name} could not be evaluated."
            ),
        )

    def run(
        self,
        assessment: Assessment,
    ) -> AssessmentAnalysis:
        """Translate deterministic findings without changing their meaning.

        The legacy Assessment contract is intentionally preserved here for
        compatibility with the legacy workflow path. Domain/category
        information already present in each deterministic finding is retained
        in ``AnalysisFinding.category`` so downstream reporting can group
        evidence by assessment area.
        """
        triggered_findings = [
            finding
            for finding in assessment.findings
            if finding.result.status == RuleStatus.TRIGGERED
        ]

        not_evaluable_results = [
            result
            for result in assessment.rule_results
            if result.status == RuleStatus.NOT_EVALUABLE
        ]

        key_findings = [
            self._to_analysis_finding(finding) for finding in triggered_findings
        ]

        risk_factors = [
            self._to_analysis_finding(finding)
            for finding in triggered_findings
            if finding.result.severity == RuleSeverity.HIGH
        ]

        limitations = [self._to_limitation(result) for result in not_evaluable_results]

        return AssessmentAnalysis(
            position_id=assessment.position_id,
            assessment_status=assessment.status,
            key_findings=key_findings,
            risk_factors=risk_factors,
            limitations=limitations,
        )
