from src.agents.workflow.workflow_factory import (
    create_default_assessment_workflow,
)
from src.llm.gemini_client import GeminiClient
from src.models.position import CreditPosition


def main():

    position = CreditPosition(
        position_id="POS001",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=GeminiClient(),
    )

    result = workflow.run(position)

    print("\nAssessment status:")
    print(result.assessment.status)

    print("\nKey findings:")
    print(result.analysis.key_findings)

    print("\nRisk factors:")
    print(result.analysis.risk_factors)

    print("\nLimitations:")
    print(result.analysis.limitations)

    print("\nGenerated report:")
    print(result.report.executive_summary)


if __name__ == "__main__":
    main()

# python -m scripts.check_gemini_workflow per eseguirlo