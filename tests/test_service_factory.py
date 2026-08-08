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

    assessment = service.assess(position)

    assert assessment.position_id == "POS001"

    assert len(assessment.comments) == 4

    assert assessment.comments[0].rule_id == "R001"
    assert assessment.comments[1].rule_id == "R002"
    assert assessment.comments[2].rule_id == "R003"
    assert assessment.comments[3].rule_id == "R004"