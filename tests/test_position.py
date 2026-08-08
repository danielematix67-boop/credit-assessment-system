from src.models.position import CreditPosition

def test_credit_position_creation():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=250000,
        profit_loss=-50000,
    )

    assert position.position_id == "POS001"
    assert position.revenue_growth == -0.15
    assert position.ebitda == 250000
    assert position.profit_loss == -50000