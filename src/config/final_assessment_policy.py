from dataclasses import dataclass
from pathlib import Path

import yaml

from src.models.assessment_section import SectionStatus


@dataclass(frozen=True)
class FinalAssessmentPolicy:
    critical_if_any_section_critical: bool
    critical_if_core_attention_at_least: int
    core_sections: frozenset[str]
    contextual_sections: frozenset[str]
    normal_if_all_evaluable_normal: bool
    normal_requires_min_evaluable_sections: int
    no_evaluable_status: SectionStatus
    partial_evaluation_message: str
    not_evaluable_message: str

    @classmethod
    def load(cls, path: Path) -> "FinalAssessmentPolicy":
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if not isinstance(data, dict) or not isinstance(data.get("policy"), dict):
            raise ValueError("Invalid final assessment policy configuration")

        policy = data["policy"]
        required = {
            "critical_if_any_section_critical",
            "critical_if_core_attention_at_least",
            "core_sections",
            "contextual_sections",
            "normal_if_all_evaluable_normal",
            "normal_requires_min_evaluable_sections",
            "no_evaluable_status",
            "partial_evaluation_message",
            "not_evaluable_message",
        }
        missing = required - policy.keys()
        if missing:
            raise ValueError(f"Missing final assessment policy fields: {sorted(missing)}")

        core_sections = policy["core_sections"]
        contextual_sections = policy["contextual_sections"]
        if not isinstance(core_sections, list) or not all(isinstance(x, str) for x in core_sections):
            raise ValueError("core_sections must be a list of strings")
        if not isinstance(contextual_sections, list) or not all(isinstance(x, str) for x in contextual_sections):
            raise ValueError("contextual_sections must be a list of strings")

        try:
            no_evaluable_status = SectionStatus(policy["no_evaluable_status"])
        except ValueError as exc:
            raise ValueError("Invalid no_evaluable_status") from exc

        minimum = policy["normal_requires_min_evaluable_sections"]
        critical_count = policy["critical_if_core_attention_at_least"]
        if not isinstance(minimum, int) or minimum < 1:
            raise ValueError("normal_requires_min_evaluable_sections must be a positive integer")
        if not isinstance(critical_count, int) or critical_count < 1:
            raise ValueError("critical_if_core_attention_at_least must be a positive integer")

        return cls(
            critical_if_any_section_critical=policy["critical_if_any_section_critical"],
            critical_if_core_attention_at_least=critical_count,
            core_sections=frozenset(core_sections),
            contextual_sections=frozenset(contextual_sections),
            normal_if_all_evaluable_normal=policy["normal_if_all_evaluable_normal"],
            normal_requires_min_evaluable_sections=minimum,
            no_evaluable_status=no_evaluable_status,
            partial_evaluation_message=policy["partial_evaluation_message"],
            not_evaluable_message=policy["not_evaluable_message"],
        )

    @classmethod
    def default(cls) -> "FinalAssessmentPolicy":
        return cls.load(Path("config/final_assessment.yaml"))
