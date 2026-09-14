from src.models.position import CreditPosition
from src.rules.base.status import RuleStatus
from src.rules.financial_analysis.r004 import NfpToEbitdaRule


def test_nfp_to_ebitda_rule():
    result = NfpToEbitdaRule().evaluate(
        CreditPosition(position_id="POS001", nfp_to_ebitda=6.0)
    )
    assert result.status == RuleStatus.TRIGGERED
    assert result.value == 6.0
