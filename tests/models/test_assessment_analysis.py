from src.models.assessment_analysis import AssessmentAnalysis


def test_assessment_analysis_can_be_created():
    analysis = AssessmentAnalysis(
        position_id="POS001",
        key_findings=["Revenue deterioration"],
        risk_factors=["High leverage"],
        limitations=["Some indicators were not evaluable"],
    )

    assert analysis.position_id == "POS001"
    assert analysis.key_findings == ["Revenue deterioration"]
    assert analysis.risk_factors == ["High leverage"]
    assert analysis.limitations == [
        "Some indicators were not evaluable"
    ]