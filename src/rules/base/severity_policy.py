from dataclasses import dataclass

from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold


@dataclass(frozen=True)
class SeverityPolicy:
    """
    Determines rule severity from a numeric value.

    Severity thresholds define severity bands.

    HIGHER_IS_WORSE:
        The highest severity threshold that is less than or equal to
        the value determines the severity.

    LOWER_IS_WORSE:
        The highest severity threshold that is greater than or equal to
        the value determines the severity.

    If no threshold applies, None is returned and the caller may
    fall back to the rule-level default severity.
    """

    direction: SeverityDirection
    thresholds: tuple[SeverityThreshold, ...]

    _SEVERITY_RANK = {
        RuleSeverity.LOW: 1,
        RuleSeverity.MEDIUM: 2,
        RuleSeverity.HIGH: 3,
    }

    def evaluate(
        self,
        value: float,
    ) -> RuleSeverity | None:
        if self.direction == SeverityDirection.HIGHER_IS_WORSE:
            applicable = [item for item in self.thresholds if value >= item.threshold]

        elif self.direction == SeverityDirection.LOWER_IS_WORSE:
            applicable = [item for item in self.thresholds if value <= item.threshold]

        else:
            raise ValueError(f"Unsupported severity direction: {self.direction}")

        if not applicable:
            return None

        return max(
            applicable,
            key=lambda item: self._SEVERITY_RANK[item.severity],
        ).severity
