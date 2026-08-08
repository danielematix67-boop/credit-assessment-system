from src.models.position import CreditPosition
from src.services.service_factory import create_default_assessment_service


def test_default_assessment_service():
    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
    )

    service = create_default_assessment_service()

    comments = service.assess(position)

    assert len(comments) == 4

    assert comments[0].rule_id == "R001"
    assert comments[1].rule_id == "R002"
    assert comments[2].rule_id == "R003"
    assert comments[3].rule_id == "R004"