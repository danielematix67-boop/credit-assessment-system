from pathlib import Path

from src.comments.comment import Comment
from src.comments.comment_engine import CommentEngine
from src.config.rule_config_loader import RuleConfigLoader
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.behavioural_data import BehaviouralData
from src.models.rule_finding import RuleFinding
from src.rules.base.status import RuleStatus
from src.rules.registry import build_rules
from src.services.assessment_status_calculator import AssessmentStatusCalculator


class BehaviouralAssessmentService:
    """Build behavioural assessment using the shared Rule implementation."""

    DEFAULT_CONFIG_PATH = Path("config/behavioural_analysis_rules.yaml")

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

    def assess(self, data: BehaviouralData) -> AssessmentSection:
        configs = self.config_loader.load(self.config_path)
        results = [rule.evaluate(data) for rule in build_rules(configs)]
        findings = []

        for result in results:
            if result.status != RuleStatus.TRIGGERED:
                continue
            comment = self.comment_engine.generate(result)
            findings.append(
                RuleFinding(
                    result=result,
                    comment=comment or Comment(result.rule_id, result.reason or ""),
                )
            )

        limitations = []
        if all(result.status == RuleStatus.NOT_EVALUABLE for result in results):
            limitations.append("Behavioural banking indicators are not available.")

        return AssessmentSection(
            name="Behavioural Analysis",
            status=SectionStatus(self.status_calculator.calculate(results).value),
            findings=findings,
            evidence=results,
            limitations=limitations,
        )
