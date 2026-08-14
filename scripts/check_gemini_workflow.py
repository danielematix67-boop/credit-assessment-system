# Run with:
# python -m scripts.check_gemini_workflow

from src.agents.workflow.workflow_factory import (
    create_default_assessment_workflow,
)
from src.llm.gemini_client import GeminiClient
from src.models.position import CreditPosition


# ============================================================
# Configuration
# ============================================================

SEPARATOR = "=" * 72
SUB_SEPARATOR = "-" * 72


# ============================================================
# Helpers
# ============================================================


def finding_signature(finding):
    """
    Normalize an analysis/report finding so that comparisons
    are independent from object representation and ordering.
    """
    return (
        finding.rule_id,
        finding.category,
        finding.severity,
        finding.text,
    )


def flatten_report_findings(report):
    """Extract report findings into normalized tuples."""
    return [
        finding_signature(finding)
        for finding_group in report.findings_by_category
        for finding in finding_group.findings
    ]


def normalize_limitations(limitations):
    """
    Normalize limitations because the report may contain either
    strings or AnalysisFinding objects.
    """
    normalized = []

    for limitation in limitations:
        if hasattr(limitation, "text"):
            normalized.append(limitation.text)
        else:
            normalized.append(str(limitation))

    return normalized


def print_check(label, passed):
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {label}")


def print_warning(message):
    print(f"  [WARN] {message}")


def print_info(message):
    print(f"  [INFO] {message}")


# ============================================================
# Scenario execution
# ============================================================


def run_scenario(
    name: str,
    position: CreditPosition,
) -> dict:

    print()
    print(SEPARATOR)
    print(f"  SCENARIO: {name}")
    print(SEPARATOR)

    # --------------------------------------------------------
    # Workflow
    # --------------------------------------------------------

    workflow = create_default_assessment_workflow(
        use_llm=True,
        llm_client=GeminiClient(),
    )

    result = workflow.run(position)

    # --------------------------------------------------------
    # LLM status
    # --------------------------------------------------------

    print("\n[0] REPORT GENERATION")
    print(SUB_SEPARATOR)

    if getattr(result.report, "generated_by_llm", False):
        print("  Generator: Gemini LLM")
    else:
        print("  Generator: Deterministic fallback")

    # --------------------------------------------------------
    # Deterministic assessment
    # --------------------------------------------------------

    print("\n[1] DETERMINISTIC ASSESSMENT")
    print(SUB_SEPARATOR)

    print(f"Status: {result.assessment.status.value}")

    triggered_rules = [
        rule_result
        for rule_result in result.assessment.rule_results
        if rule_result.status.value == "TRIGGERED"
    ]

    print("\nTriggered rules:")

    if triggered_rules:
        for rule_result in triggered_rules:
            print(
                f"  - {rule_result.rule_id}: "
                f"{rule_result.rule_name}"
            )
    else:
        print("  - None")

    not_evaluable_rules = [
        rule_result
        for rule_result in result.assessment.rule_results
        if rule_result.status.value == "NOT_EVALUABLE"
    ]

    if not_evaluable_rules:
        print("\nNot evaluable:")

        for rule_result in not_evaluable_rules:
            print(
                f"  - {rule_result.rule_id}: "
                f"{rule_result.rule_name}"
            )

    # --------------------------------------------------------
    # Analysis agent
    # --------------------------------------------------------

    print("\n[2] ANALYSIS AGENT")
    print(SUB_SEPARATOR)

    analysis_findings = [
        finding_signature(finding)
        for finding in result.analysis.key_findings
    ]

    print(f"Key findings: {len(analysis_findings)}")

    for finding in result.analysis.key_findings:
        print(
            f"  - [{finding.rule_id}] "
            f"{finding.severity.value:<6} | "
            f"{finding.category}"
        )
        print(f"    {finding.text}")

    print(
        f"\nRisk factors: "
        f"{len(result.analysis.risk_factors)}"
    )

    for risk in result.analysis.risk_factors:
        print(
            f"  - [{risk.rule_id}] "
            f"{risk.severity.value:<6} | "
            f"{risk.text}"
        )

    print(
        f"\nLimitations: "
        f"{len(result.analysis.limitations)}"
    )

    for limitation in result.analysis.limitations:
        print(
            f"  - [{limitation.rule_id}] "
            f"{limitation.text}"
        )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print("\n[3] REPORT")
    print(SUB_SEPARATOR)

    print("Executive summary:")
    print(f"  {result.report.executive_summary}")

    report_findings = flatten_report_findings(result.report)

    report_limitations = normalize_limitations(
        result.report.limitations
    )

    print(f"\nReport findings: {len(report_findings)}")

    for finding in report_findings:
        rule_id, category, severity, text = finding

        print(
            f"  - [{rule_id}] "
            f"{severity.value:<6} | "
            f"{category}"
        )
        print(f"    {text}")

    print(
        f"\nReport limitations: "
        f"{len(report_limitations)}"
    )

    for limitation in report_limitations:
        print(f"  - {limitation}")

    # --------------------------------------------------------
    # Consistency checks
    # --------------------------------------------------------

    print("\n[4] CONSISTENCY CHECKS")
    print(SUB_SEPARATOR)

    # 1. Assessment status

    status_consistent = (
        result.assessment.status
        == result.analysis.assessment_status
        == result.report.assessment_status
    )

    print_check(
        "Assessment status preserved",
        status_consistent,
    )

    # 2. Findings

    analysis_findings_set = set(analysis_findings)
    report_findings_set = set(report_findings)

    findings_consistent = (
        analysis_findings_set
        == report_findings_set
    )

    print_check(
        "Analysis -> Report findings preserved",
        findings_consistent,
    )

    # 3. Limitations

    analysis_limitations = normalize_limitations(
        result.analysis.limitations
    )

    limitations_consistent = (
        set(analysis_limitations)
        == set(report_limitations)
    )

    print_check(
        "Limitations preserved",
        limitations_consistent,
    )

    # 4. Risk factors

    triggered_rule_ids = {
        rule_result.rule_id
        for rule_result in result.assessment.rule_results
        if rule_result.status.value == "TRIGGERED"
    }

    risk_factor_rule_ids = {
        risk.rule_id
        for risk in result.analysis.risk_factors
    }

    risk_factors_traceable = (
        risk_factor_rule_ids.issubset(
            triggered_rule_ids
        )
    )

    print_check(
        "Risk factors traceable to triggered rules",
        risk_factors_traceable,
    )

    # --------------------------------------------------------
    # Diagnostics
    # --------------------------------------------------------

    if not findings_consistent:
        print("\n  Finding mismatch:")

        missing_from_report = (
            analysis_findings_set
            - report_findings_set
        )

        unexpected_in_report = (
            report_findings_set
            - analysis_findings_set
        )

        if missing_from_report:
            print("  Missing from report:")

            for finding in sorted(
                missing_from_report,
                key=lambda x: x[0],
            ):
                print(
                    f"    - [{finding[0]}] "
                    f"{finding[3]}"
                )

        if unexpected_in_report:
            print("  Unexpected in report:")

            for finding in sorted(
                unexpected_in_report,
                key=lambda x: x[0],
            ):
                print(
                    f"    - [{finding[0]}] "
                    f"{finding[3]}"
                )

    if not limitations_consistent:
        print("\n  Limitation mismatch:")

        missing_limitations = (
            set(analysis_limitations)
            - set(report_limitations)
        )

        unexpected_limitations = (
            set(report_limitations)
            - set(analysis_limitations)
        )

        if missing_limitations:
            print("  Missing from report:")

            for limitation in sorted(
                missing_limitations
            ):
                print(
                    f"    - {limitation}"
                )

        if unexpected_limitations:
            print("  Unexpected in report:")

            for limitation in sorted(
                unexpected_limitations
            ):
                print(
                    f"    - {limitation}"
                )

    # --------------------------------------------------------
    # Scenario result
    # --------------------------------------------------------

    scenario_passed = all(
        [
            status_consistent,
            findings_consistent,
            limitations_consistent,
            risk_factors_traceable,
        ]
    )

    print("\n" + SUB_SEPARATOR)

    if scenario_passed:
        print(f"  RESULT: PASS - {name}")
    else:
        print(f"  RESULT: FAIL - {name}")

    print(SUB_SEPARATOR)

    return {
        "name": name,
        "passed": scenario_passed,
        "status": status_consistent,
        "findings": findings_consistent,
        "limitations": limitations_consistent,
        "risk_factors": risk_factors_traceable,
    }


# ============================================================
# Main
# ============================================================


def main():

    print(SEPARATOR)
    print("  CREDIT ASSESSMENT WORKFLOW CHECK")
    print(SEPARATOR)

    print()
    print_info(
        "Testing deterministic assessment, analysis, "
        "report generation and consistency."
    )
    print_info(
        "LLM generation is optional; deterministic fallback "
        "must preserve all critical information."
    )

    # --------------------------------------------------------
    # Scenarios
    # --------------------------------------------------------

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

    scenarios = [
        ("CRITICAL", critical_position),
        ("ATTENTION", attention_position),
        ("NORMAL", normal_position),
    ]

    results = []

    # --------------------------------------------------------
    # Run scenarios
    # --------------------------------------------------------

    for name, position in scenarios:
        results.append(
            run_scenario(
                name,
                position,
            )
        )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print(SEPARATOR)
    print("  FINAL SUMMARY")
    print(SEPARATOR)

    for result in results:
        status = (
            "PASS"
            if result["passed"]
            else "FAIL"
        )

        print(
            f"  [{status}] "
            f"{result['name']:<10} | "
            f"status={result['status']} | "
            f"findings={result['findings']} | "
            f"limitations={result['limitations']} | "
            f"risks={result['risk_factors']}"
        )

    all_passed = all(
        result["passed"]
        for result in results
    )

    print()

    if all_passed:
        print(
            "  OVERALL RESULT: PASS"
        )
        print(
            "  Deterministic integrity preserved."
        )
    else:
        print(
            "  OVERALL RESULT: FAIL"
        )
        print(
            "  One or more integrity checks failed."
        )

    print(SEPARATOR)


if __name__ == "__main__":
    main()
