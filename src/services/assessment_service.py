from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.models.position import CreditPosition
from src.models.assessment import Assessment
from src.services.assessment_status_calculator import AssessmentStatusCalculator

# AssessmentService orchestrates the assessment workflow.
#
# It coordinates rule evaluation, assessment status calculation,
# and comment generation without implementing business rules itself.
#
# The service returns the complete assessment for a CreditPosition.

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

        comments = []

        for result in results:
            comment = self.comment_engine.generate(result)

            if comment is not None:
                comments.append(comment)

        status = self.status_calculator.calculate(results)

        return Assessment(
            position_id=position.position_id,
            rule_results=results,
            comments=comments,
            status=status,
        )
