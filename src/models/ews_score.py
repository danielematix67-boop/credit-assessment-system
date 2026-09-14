from enum import Enum


class EwsScoreClass(str, Enum):
    """Colour class assigned by the Early Warning System score."""

    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    LIGHT_RED = "LIGHT_RED"
