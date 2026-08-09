from src.models.assessment_status import AssessmentStatus


def test_assessment_status_values():
    assert AssessmentStatus.NORMAL.value == "NORMAL"
    assert AssessmentStatus.ATTENTION.value == "ATTENTION"
    assert AssessmentStatus.CRITICAL.value == "CRITICAL"


def test_assessment_status_members():
    assert list(AssessmentStatus) == [
        AssessmentStatus.NORMAL,
        AssessmentStatus.ATTENTION,
        AssessmentStatus.CRITICAL,
    ]

