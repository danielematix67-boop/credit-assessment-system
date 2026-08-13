from src.agents.workflow.workflow_factory import (
    create_default_assessment_workflow,
)
from src.llm.gemini_client import GeminiClient
from src.models.position import CreditPosition


def run_scenario(
    name: str,
    position: CreditPosition,
) -> None:
    print("\n" + "=" * 70)
    print(f"SCENARIO: {name}")
    print("=" * 70)

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


def main():
    critical_position = CreditPosition(
        position_id="POS_CRITICAL",
        revenue_growth=-0.15,
        ebitda=-50000,
        profit_loss=-50000,
        ebitda_margin=-0.05,
        pfn_to_ebitda=6.0,
        interest_expense=40000,
    )

    attention_position = CreditPosition(
        position_id="POS_ATTENTION",
        revenue_growth=-0.15,
        ebitda=100000,
        profit_loss=20000,
        ebitda_margin=0.05,
        pfn_to_ebitda=4.0,
        interest_expense=20000,
    )

    normal_position = CreditPosition(
        position_id="POS_NORMAL",
        revenue_growth=0.05,
        ebitda=250000,
        profit_loss=100000,
        ebitda_margin=0.15,
        pfn_to_ebitda=2.0,
        interest_expense=10000,
    )

    run_scenario(
        "CRITICAL",
        critical_position,
    )

    run_scenario(
        "ATTENTION",
        attention_position,
    )

    run_scenario(
        "NORMAL",
        normal_position,
    )


if __name__ == "__main__":
    main()