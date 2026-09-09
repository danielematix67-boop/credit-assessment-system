import pytest

from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus


def test_assessment_analysis_can_be_created():
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=["Revenue deterioration"],
        risk_factors=["High leverage"],
        limitations=["Some indicators were not evaluable"],
    )

    assert analysis.position_id == "POS001"
    assert analysis.assessment_status == AssessmentStatus.CRITICAL
    assert analysis.key_findings == ["Revenue deterioration"]
    assert analysis.risk_factors == ["High leverage"]
    assert analysis.limitations == ["Some indicators were not evaluable"]


def test_assessment_analysis_is_immutable():
    analysis = AssessmentAnalysis(
        position_id="POS001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=["Revenue deterioration"],
        risk_factors=["High leverage"],
        limitations=["Some indicators were not evaluable"],
    )

    with pytest.raises(AttributeError):
        analysis.assessment_status = AssessmentStatus.NORMAL
