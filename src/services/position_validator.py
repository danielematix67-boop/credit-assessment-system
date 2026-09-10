import math
from dataclasses import fields

from src.models.position import CreditPosition


class CreditPositionValidator:
    """Validate the structural integrity of a credit position before assessment."""

    def validate(self, position: CreditPosition) -> None:
        """Raise ValueError when the position cannot be safely assessed."""
        if not isinstance(position, CreditPosition):
            raise TypeError("position must be a CreditPosition instance")

        if not position.position_id or not position.position_id.strip():
            raise ValueError("position_id must be a non-empty string")

        for field in fields(position):
            value = getattr(position, field.name)

            if field.name == "position_id" or value is None:
                continue

            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"{field.name} must be a numeric value or None"
                )

            if not math.isfinite(value):
                raise ValueError(
                    f"{field.name} must be finite (NaN and infinite values are not allowed)"
                )
