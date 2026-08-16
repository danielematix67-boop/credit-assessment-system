from enum import Enum


class SeverityDirection(str, Enum):
    """
    Defines how severity thresholds are interpreted.
    """

    LOWER_IS_WORSE = "LOWER_IS_WORSE"
    HIGHER_IS_WORSE = "HIGHER_IS_WORSE"