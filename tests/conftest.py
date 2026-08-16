import pytest

from src.comments.comment_engine import CommentEngine
from src.engine.rule_engine import RuleEngine
from src.services.assessment_service import AssessmentService
from src.services.assessment_status_calculator import (
    AssessmentStatusCalculator,
)
from src.rules.registry import get_default_rules


@pytest.fixture
def assessment_service() -> AssessmentService:
    return AssessmentService(
        rule_engine=RuleEngine(get_default_rules()),
        comment_engine=CommentEngine(),
        status_calculator=AssessmentStatusCalculator(),
    )