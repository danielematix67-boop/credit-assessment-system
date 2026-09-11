from pathlib import Path

import yaml

from src.config.final_assessment_policy import FinalAssessmentPolicy
from src.models.assessment_section import AssessmentSection, SectionStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.position import CreditPosition
from src.services.final_assessment_service import FinalAssessmentService


def _section(name: str, status: SectionStatus) -> AssessmentSection:
    return AssessmentSection(name=name, status=status, findings=[], evidence=[], limitations=[])


def _case(*statuses: SectionStatus) -> CreditAssessmentCase:
    sections = list(statuses) + [SectionStatus.NOT_EVALUABLE] * (4 - len(statuses))
    return CreditAssessmentCase(
        position=CreditPosition(position_id="TEST"),
        customer_profile=_section("Customer Profile", sections[0]),
        financial_analysis=_section("Financial Analysis", sections[1]),
        behavioural_analysis=_section("Behavioural Analysis", sections[2]),
        debt_sustainability=_section("Debt Sustainability", sections[3]),
    )


def test_changing_core_attention_threshold_changes_final_status_without_code_change(
    tmp_path: Path,
) -> None:
    raw = yaml.safe_load(Path("config/final_assessment.yaml").read_text(encoding="utf-8"))
    raw["policy"]["critical_if_core_attention_at_least"] = 3
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    policy = FinalAssessmentPolicy.load(path)
    result = FinalAssessmentService(policy).assess(
        _case(
            SectionStatus.NORMAL,
            SectionStatus.ATTENTION,
            SectionStatus.ATTENTION,
        )
    )

    assert result.status == SectionStatus.ATTENTION
