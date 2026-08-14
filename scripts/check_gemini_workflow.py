# python -m scripts.check_gemini_workflow

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

    print("\n--- DETERMINISTIC ASSESSMENT ---")

    print("\nAssessment status:")
    print(result.assessment.status)

    print("\nRule results:")
    for rule_result in result.assessment.rule_results:
        print(
            f"- {rule_result.rule_id}: "
            f"{rule_result.rule_name} | "
            f"{rule_result.status.value}"
        )

    print("\nComments:")
    for finding in result.assessment.findings:
        print(
            f"- [{finding.comment.rule_id}] "
            f"{finding.comment.text}"
        )

    print("\n--- ANALYSIS AGENT ---")

    print("\nKey findings:")
    for finding in result.analysis.key_findings:
        print(f"- {finding}")

    print("\nRisk factors:")
    for risk in result.analysis.risk_factors:
        print(f"- {risk}")

    print("\nLimitations:")
    for limitation in result.analysis.limitations:
        print(f"- {limitation}")

    print("\n--- LLM REPORT ---")

    print("\nGenerated executive summary:")
    print(result.report.executive_summary)

    print("\n--- CONSISTENCY CHECKS ---")

    status_consistent = (
        result.assessment.status
        == result.analysis.assessment_status
        == result.report.assessment_status
    )

    findings_consistent = (
        result.analysis.key_findings
        == result.report.findings
    )

    limitations_consistent = (
        result.analysis.limitations
        == result.report.limitations
    )

    print(
        f"Assessment status preserved: "
        f"{'PASS' if status_consistent else 'FAIL'}"
    )

    print(
        f"Findings preserved: "
        f"{'PASS' if findings_consistent else 'FAIL'}"
    )

    print(
        f"Limitations preserved: "
        f"{'PASS' if limitations_consistent else 'FAIL'}"
    )


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

