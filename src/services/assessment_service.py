from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.models.assessment import Assessment
from src.models.position import CreditPosition
from src.models.rule_finding import RuleFinding
from src.services.assessment_status_calculator import AssessmentStatusCalculator


class AssessmentService:
    def __init__(
        self,
        rule_engine: RuleEngine,
        comment_engine: CommentEngine,
        status_calculator: AssessmentStatusCalculator,
    ):
        self.rule_engine = rule_engine
        self.comment_engine = comment_engine
        self.status_calculator = status_calculator

    def assess(self, position: CreditPosition) -> Assessment:
        results = self.rule_engine.evaluate(position)

        findings = []

        for result in results:
            comment = self.comment_engine.generate(result)

            if comment is not None:
                findings.append(
                    RuleFinding(
                        result=result,
                        comment=comment,
                    )
                )

        status = self.status_calculator.calculate(results)

        return Assessment(
            position_id=position.position_id,
            rule_results=results,
            findings=findings,
            status=status,
        )
