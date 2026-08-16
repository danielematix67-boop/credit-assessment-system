from src.models.assessment_status import AssessmentStatus


def test_assessment_status_contains_members():
    statuses = list(AssessmentStatus)

    assert statuses
    assert all(
        isinstance(status, AssessmentStatus)
        for status in statuses
    )


def test_assessment_status_members_have_string_values():
    for status in AssessmentStatus:
        assert isinstance(status.value, str)
        assert status.value


def test_assessment_status_members_have_unique_values():
    values = [
        status.value
        for status in AssessmentStatus
    ]

    assert len(values) == len(set(values))