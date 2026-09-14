from pathlib import Path
from typing import cast

from src.comments.comment_engine import CommentEngine
from src.config.rule_config_loader import RuleConfigLoader
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.debt_sustainability_data import DebtSustainabilityData
from src.models.position import CreditPosition
from src.models.rule_finding import RuleFinding
from src.rules.base.status import RuleStatus
from src.rules.registry import build_rules
from src.rules.result import RuleResult
from src.services.assessment_status_calculator import AssessmentStatusCalculator


class DebtSustainabilityAssessmentService:
    """Assess debt sustainability using the shared Rule implementation."""

    DEFAULT_CONFIG_PATH = Path("config/debt_sustainability_rules.yaml")

    def __init__(
        self,
        status_calculator: AssessmentStatusCalculator | None = None,
        comment_engine: CommentEngine | None = None,
        config_loader: RuleConfigLoader | None = None,
        config_path: Path | None = None,
    ) -> None:
        self.status_calculator = status_calculator or AssessmentStatusCalculator()
        self.comment_engine = comment_engine or CommentEngine()
        self.config_loader = config_loader or RuleConfigLoader()
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH

    def assess(self, data: DebtSustainabilityData) -> AssessmentSection:
        configs = self.config_loader.load(self.config_path)
        results = [
            rule.evaluate(cast(CreditPosition, data)) for rule in build_rules(configs)
        ]
        status = self._section_status(results)
        findings = []
        for result in results:
            if result.status != RuleStatus.TRIGGERED:
                continue
            comment = self.comment_engine.generate(result)
            if comment is not None:
                findings.append(RuleFinding(result=result, comment=comment))

        limitations = (
            ["Debt-service and cash-flow data are not available."]
            if all(result.status == RuleStatus.NOT_EVALUABLE for result in results)
            else [
                "Debt sustainability is assessed from the supplied synthetic inputs only."
            ]
        )
        return AssessmentSection(
            name="Debt Sustainability",
            status=status,
            findings=findings,
            evidence=results,
            limitations=limitations,
        )

    @staticmethod
    def _section_status(results: list[RuleResult]) -> SectionStatus:
        evaluable = [
            result for result in results if result.status != RuleStatus.NOT_EVALUABLE
        ]
        if not evaluable:
            return SectionStatus.ATTENTION

        triggered = {
            result.rule_id
            for result in evaluable
            if result.status == RuleStatus.TRIGGERED
        }
        if not triggered:
            return SectionStatus.NORMAL

        # DS001 and DS003 describe the same CFADS/debt-service weakness.
        independent_leverage_trigger = "DS002" in triggered
        cash_flow_trigger = bool(triggered & {"DS001", "DS003"})
        if independent_leverage_trigger and cash_flow_trigger:
            return SectionStatus.CRITICAL
        return SectionStatus.ATTENTION
