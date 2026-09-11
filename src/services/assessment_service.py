from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.models.financial_assessment import FinancialAssessment
from src.models.position import CreditPosition
from src.models.rule_finding import RuleFinding
from src.services.assessment_status_calculator import AssessmentStatusCalculator
from src.services.position_validator import CreditPositionValidator


class AssessmentService:
    """Run the deterministic financial rule engine for a credit position."""

    def __init__(
        self,
        rule_engine: RuleEngine,
        comment_engine: CommentEngine,
        status_calculator: AssessmentStatusCalculator,
        position_validator: CreditPositionValidator | None = None,
    ) -> None:
        self.rule_engine = rule_engine
        self.comment_engine = comment_engine
        self.status_calculator = status_calculator
        self.position_validator = position_validator or CreditPositionValidator()

    def assess(self, position: CreditPosition) -> FinancialAssessment:
        self.position_validator.validate(position)
        results = self.rule_engine.evaluate(position)

        findings: list[RuleFinding] = []
        for result in results:
            comment = self.comment_engine.generate(result)
            if comment is not None:
                findings.append(RuleFinding(result=result, comment=comment))

        status = self.status_calculator.calculate(results)
        return FinancialAssessment(
            position_id=position.position_id,
            rule_results=results,
            findings=findings,
            status=status,
        )
