from pathlib import Path

import pytest
from src.config.final_assessment_policy import FinalAssessmentPolicy
from src.models.assessment_section import SectionStatus


CONFIG_PATH = Path("config/final_assessment.yaml")


def test_default_policy_matches_current_deterministic_policy() -> None:
    policy = FinalAssessmentPolicy.default()

    assert policy.critical_if_any_section_critical is True
    assert policy.critical_if_core_attention_at_least == 2
    assert policy.core_sections == frozenset(
        {"Financial Analysis", "Behavioural Analysis", "Debt Sustainability"}
    )
    assert policy.contextual_sections == frozenset({"Customer Profile"})
    assert policy.no_evaluable_status == SectionStatus.ATTENTION


def test_policy_rejects_missing_required_field(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text("policy:\n  core_sections: []\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing final assessment policy fields"):
        FinalAssessmentPolicy.load(path)


def test_policy_rejects_invalid_status(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(
        """policy:
  critical_if_any_section_critical: true
  critical_if_core_attention_at_least: 2
  core_sections: []
  contextual_sections: []
  normal_if_all_evaluable_normal: true
  normal_requires_min_evaluable_sections: 2
  no_evaluable_status: INVALID
  partial_evaluation_message: test
  not_evaluable_message: test
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid no_evaluable_status"):
        FinalAssessmentPolicy.load(path)


def test_policy_rejects_non_positive_core_attention_threshold(tmp_path: Path) -> None:
    content = CONFIG_PATH.read_text(encoding="utf-8").replace(
        "critical_if_core_attention_at_least: 2",
        "critical_if_core_attention_at_least: 0",
    )
    path = tmp_path / "invalid.yaml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="critical_if_core_attention_at_least"):
        FinalAssessmentPolicy.load(path)
