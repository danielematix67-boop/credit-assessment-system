import math

import pytest

from src.models.position import CreditPosition
from src.services.position_validator import CreditPositionValidator


@pytest.fixture
def validator():
    return CreditPositionValidator()


def test_valid_position_is_accepted(validator):
    position = CreditPosition(
        position_id="VALID_POSITION",
        revenue=1_000_000,
        ebitda=100_000,
        revenue_growth=0.05,
        nfp_to_ebitda=3.5,
    )

    validator.validate(position)


def test_blank_position_id_is_rejected(validator):
    with pytest.raises(ValueError, match="position_id"):
        validator.validate(CreditPosition(position_id="   "))


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_numeric_values_are_rejected(validator, value):
    position = CreditPosition(
        position_id="INVALID_POSITION",
        revenue_growth=value,
    )

    with pytest.raises(ValueError, match="finite"):
        validator.validate(position)


def test_non_numeric_values_are_rejected(validator):
    position = CreditPosition(
        position_id="INVALID_POSITION",
        ebitda="100000",
    )

    with pytest.raises(ValueError, match="numeric"):
        validator.validate(position)


def test_wrong_position_type_is_rejected(validator):
    with pytest.raises(TypeError, match="CreditPosition"):
        validator.validate({"position_id": "INVALID"})
