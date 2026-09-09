from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.rules.registry import get_default_rules
from src.services.assessment_service import AssessmentService
from src.services.assessment_status_calculator import AssessmentStatusCalculator


def create_default_assessment_service() -> AssessmentService:
    rules = get_default_rules()

    rule_engine = RuleEngine(rules)
    comment_engine = CommentEngine()
    status_calculator = AssessmentStatusCalculator()

    return AssessmentService(
        rule_engine=rule_engine,
        comment_engine=comment_engine,
        status_calculator=status_calculator,
    )
