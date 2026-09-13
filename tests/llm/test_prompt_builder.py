from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.rules.base.severity import RuleSeverity


def make_finding(
    rule_id: str,
    category: str,
    severity: RuleSeverity,
    text: str,
) -> AnalysisFinding:
    return AnalysisFinding(
        rule_id=rule_id,
        category=category,
        severity=severity,
        text=text,
    )


def make_analysis(
    key_findings: list[AnalysisFinding] | None = None,
    rule_evidence: list[AnalysisFinding] | None = None,
) -> AssessmentAnalysis:
    return AssessmentAnalysis(
        position_id="TEST-001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=key_findings or [],
        risk_factors=[],
        limitations=[],
        rule_evidence=rule_evidence or [],
    )


class TestReportPromptBuilder:
    def test_build_uses_analysis_findings(self) -> None:
        finding = make_finding(
            "R001",
            "Financial Analysis",
            RuleSeverity.HIGH,
            "Revenue growth declined by 20.0%.",
        )

        prompt = ReportPromptBuilder().build(make_analysis(key_findings=[finding]))

        assert "ANALYSIS FINDINGS:" in prompt
        assert "Financial Analysis:" in prompt
        assert "[HIGH] Revenue growth declined by 20.0%." in prompt

    def test_build_orders_macro_areas_authoritatively(self) -> None:
        findings = [
            make_finding(
                "DS001",
                "Debt Sustainability",
                RuleSeverity.HIGH,
                "Debt sustainability finding.",
            ),
            make_finding(
                "B001",
                "Behavioural Analysis",
                RuleSeverity.HIGH,
                "Behavioural finding.",
            ),
            make_finding(
                "R001",
                "Financial Analysis",
                RuleSeverity.HIGH,
                "Financial finding.",
            ),
            make_finding(
                "CP001",
                "Customer Profile",
                RuleSeverity.HIGH,
                "Customer profile finding.",
            ),
        ]

        prompt = ReportPromptBuilder().build(make_analysis(key_findings=findings))

        customer = prompt.index("Customer Profile:")
        financial = prompt.index("Financial Analysis:")
        behavioural = prompt.index("Behavioural Analysis:")
        sustainability = prompt.index("Debt Sustainability:")

        assert customer < financial < behavioural < sustainability

        order_start = prompt.index("REQUIRED CATEGORY ORDER:")
        order_end = prompt.index("ANALYSIS FINDINGS:")
        category_order = prompt[order_start:order_end]
        assert category_order.index("1. Customer Profile") < category_order.index(
            "2. Financial Analysis"
        )
        assert category_order.index("2. Financial Analysis") < category_order.index(
            "3. Behavioural Analysis"
        )
        assert category_order.index("3. Behavioural Analysis") < category_order.index(
            "4. Debt Sustainability"
        )

    def test_build_preserves_finding_order_within_macro_area(self) -> None:
        findings = [
            make_finding(
                "R001",
                "Financial Analysis",
                RuleSeverity.LOW,
                "First financial finding.",
            ),
            make_finding(
                "R002",
                "Financial Analysis",
                RuleSeverity.HIGH,
                "Second financial finding.",
            ),
        ]

        prompt = ReportPromptBuilder().build(make_analysis(key_findings=findings))

        assert prompt.index("First financial finding.") < prompt.index(
            "Second financial finding."
        )

    def test_build_does_not_include_rule_ids_or_assessment_status(self) -> None:
        finding = make_finding(
            "R001",
            "Financial Analysis",
            RuleSeverity.HIGH,
            "Revenue growth declined by 20.0%.",
        )

        prompt = ReportPromptBuilder().build(make_analysis(key_findings=[finding]))

        assert "R001" not in prompt
        assert "CRITICAL" not in prompt
        assert "Assessment status" not in prompt

    def test_build_uses_complete_evidence_when_available(self) -> None:
        key_finding = make_finding(
            "R001",
            "Financial Analysis",
            RuleSeverity.HIGH,
            "Triggered financial finding.",
        )
        evidence = make_finding(
            "R002",
            "Financial Analysis",
            RuleSeverity.MEDIUM,
            "Additional deterministic evidence.",
        )

        prompt = ReportPromptBuilder().build(
            make_analysis(
                key_findings=[key_finding],
                rule_evidence=[key_finding, evidence],
            )
        )

        assert "Triggered financial finding." in prompt
        assert "Additional deterministic evidence." in prompt

    def test_build_contains_order_and_grounding_contract(self) -> None:
        finding = make_finding(
            "CP001",
            "Customer Profile",
            RuleSeverity.MEDIUM,
            "Customer profile context is available.",
        )

        prompt = ReportPromptBuilder().build(make_analysis(key_findings=[finding]))

        assert "Follow the supplied category order exactly." in prompt
        assert "The supplied Analysis findings are the sole factual source." in prompt
        assert "Do not calculate, infer, round, convert or derive new indicators." in prompt
        assert "Return ONLY the final executive narrative" in prompt

    def test_build_returns_none_when_no_findings(self) -> None:
        prompt = ReportPromptBuilder().build(make_analysis())

        assert "ANALYSIS FINDINGS:" in prompt
        assert "None." in prompt
