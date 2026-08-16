from dataclasses import dataclass

from src.rules.base.severity import RuleSeverity


@dataclass(frozen=True)
class SeverityThreshold:
    """
    Defines a threshold associated with a rule severity.

    The meaning of the threshold depends on the direction
    defined by the rule's severity policy.
    """

    threshold: float
    severity: RuleSeverity