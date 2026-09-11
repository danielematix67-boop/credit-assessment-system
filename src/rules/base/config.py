from dataclasses import dataclass

from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold


@dataclass(frozen=True)
class RuleConfig:
    rule_id: str
    rule_name: str
    category: str
    threshold: float
    severity: RuleSeverity
    severity_direction: SeverityDirection = SeverityDirection.HIGHER_IS_WORSE
    severity_thresholds: tuple[SeverityThreshold, ...] = ()
    indicator: str = ""
    input_field: str = ""
    input_fields: tuple[str, ...] = ()
    calculation: str = "direct"
    comment_template: str = ""
    trigger_operator: str = "GT"

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id cannot be empty")
        if not self.rule_name.strip():
            raise ValueError("rule_name cannot be empty")
        if not self.category.strip():
            raise ValueError("category cannot be empty")
        if self.indicator and not self.indicator.strip():
            raise ValueError("indicator cannot be blank")
        if self.input_field and not self.input_field.strip():
            raise ValueError("input_field cannot be blank")
        if any(not field.strip() for field in self.input_fields):
            raise ValueError("input_fields cannot contain blank values")
        if self.calculation not in {"direct", "ratio", "difference"}:
            raise ValueError("calculation must be one of: direct, difference, ratio")
        if self.comment_template and not self.comment_template.strip():
            raise ValueError("comment_template cannot be blank")
        valid_operators = {"GT", "GTE", "LT", "LTE"}
        if self.trigger_operator not in valid_operators:
            raise ValueError(
                "trigger_operator must be one of: "
                + ", ".join(sorted(valid_operators))
            )
