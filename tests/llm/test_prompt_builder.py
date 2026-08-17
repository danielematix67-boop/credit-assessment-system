from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.rules.base.severity import RuleSeverity
from src.models.assessment_status import AssessmentStatus


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
    risk_factors: list[AnalysisFinding] | None = None,
    limitations: list[AnalysisFinding] | None = None,
) -> AssessmentAnalysis:
    return AssessmentAnalysis(
        position_id="TEST-001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=key_findings or [],
        risk_factors=risk_factors or [],
        limitations=limitations or [],
    )


class TestReportPromptBuilder:

    def test_build_includes_deterministic_findings(self) -> None:
        finding = make_finding(
            rule_id="R001",
            category="Revenue",
            severity=RuleSeverity.HIGH,
            text="Revenue growth declined by 20.0%.",
        )

        analysis = make_analysis(
            key_findings=[finding],
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert "DETERMINISTIC ASSESSMENT FINDINGS:" in prompt
        assert "Revenue:" in prompt
        assert "[HIGH] Revenue growth declined by 20.0%." in prompt

    def test_build_groups_findings_by_category(self) -> None:
        revenue_finding = make_finding(
            rule_id="R001",
            category="Revenue",
            severity=RuleSeverity.HIGH,
            text="Revenue growth declined by 20.0%.",
        )

        profitability_finding = make_finding(
            rule_id="R002",
            category="Profitability",
            severity=RuleSeverity.HIGH,
            text="EBITDA is negative at €-120,000.",
        )

        leverage_finding = make_finding(
            rule_id="R003",
            category="Leverage",
            severity=RuleSeverity.HIGH,
            text="NFP to EBITDA is 7.0x.",
        )

        analysis = make_analysis(
            key_findings=[
                revenue_finding,
                profitability_finding,
                leverage_finding,
            ],
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert "Revenue:" in prompt
        assert "Profitability:" in prompt
        assert "Leverage:" in prompt

        assert (
            "- [HIGH] Revenue growth declined by 20.0%."
            in prompt
        )

        assert (
            "- [HIGH] EBITDA is negative at €-120,000."
            in prompt
        )

        assert (
            "- [HIGH] NFP to EBITDA is 7.0x."
            in prompt
        )

    def test_build_groups_multiple_findings_in_same_category(
        self,
    ) -> None:
        ebitda_finding = make_finding(
            rule_id="R002",
            category="Profitability",
            severity=RuleSeverity.HIGH,
            text="EBITDA is negative at €-120,000.",
        )

        interest_coverage_finding = make_finding(
            rule_id="R005",
            category="Profitability",
            severity=RuleSeverity.HIGH,
            text="Interest coverage ratio is -0.2x.",
        )

        analysis = make_analysis(
            key_findings=[
                ebitda_finding,
                interest_coverage_finding,
            ],
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert prompt.count("Profitability:") == 1

        assert (
            "- [HIGH] EBITDA is negative at €-120,000."
            in prompt
        )

        assert (
            "- [HIGH] Interest coverage ratio is -0.2x."
            in prompt
        )

    def test_build_orders_findings_by_severity(self) -> None:
        low_finding = make_finding(
            rule_id="R003",
            category="Profitability",
            severity=RuleSeverity.LOW,
            text="Minor profitability concern.",
        )

        high_finding = make_finding(
            rule_id="R001",
            category="Profitability",
            severity=RuleSeverity.HIGH,
            text="EBITDA is negative.",
        )

        medium_finding = make_finding(
            rule_id="R002",
            category="Profitability",
            severity=RuleSeverity.MEDIUM,
            text="Profit margin decreased.",
        )

        analysis = make_analysis(
            key_findings=[
                low_finding,
                high_finding,
                medium_finding,
            ],
        )

        prompt = ReportPromptBuilder().build(analysis)

        high_position = prompt.index(
            "[HIGH] EBITDA is negative.",
        )

        medium_position = prompt.index(
            "[MEDIUM] Profit margin decreased.",
        )

        low_position = prompt.index(
            "[LOW] Minor profitability concern.",
        )

        assert high_position < medium_position
        assert medium_position < low_position

    def test_build_preserves_order_for_same_severity(self) -> None:
        first_finding = make_finding(
            rule_id="R001",
            category="Profitability",
            severity=RuleSeverity.HIGH,
            text="First profitability concern.",
        )

        second_finding = make_finding(
            rule_id="R002",
            category="Profitability",
            severity=RuleSeverity.HIGH,
            text="Second profitability concern.",
        )

        analysis = make_analysis(
            key_findings=[
                first_finding,
                second_finding,
            ],
        )

        prompt = ReportPromptBuilder().build(analysis)

        first_position = prompt.index(
            "First profitability concern.",
        )

        second_position = prompt.index(
            "Second profitability concern.",
        )

        assert first_position < second_position

    def test_build_does_not_include_rule_ids(self) -> None:
        finding = make_finding(
            rule_id="R001",
            category="Revenue",
            severity=RuleSeverity.HIGH,
            text="Revenue growth declined by 20.0%.",
        )

        analysis = make_analysis(
            key_findings=[finding],
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert "R001" not in prompt
        assert "Rule ID:" not in prompt

    def test_build_does_not_duplicate_risk_factors(self) -> None:
        finding = make_finding(
            rule_id="R001",
            category="Revenue",
            severity=RuleSeverity.HIGH,
            text="Revenue growth declined by 20.0%.",
        )

        analysis = make_analysis(
            key_findings=[finding],
            risk_factors=[finding],
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert prompt.count(
            "Revenue growth declined by 20.0%.",
        ) == 1

    def test_build_excludes_assessment_status(self) -> None:
        finding = make_finding(
            rule_id="R001",
            category="Revenue",
            severity=RuleSeverity.HIGH,
            text="Revenue growth declined by 20.0%.",
        )

        analysis = make_analysis(
            key_findings=[finding],
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert "CRITICAL" not in prompt
        assert "Assessment status:" not in prompt

    def test_build_excludes_limitations(self) -> None:
        finding = make_finding(
            rule_id="R001",
            category="Revenue",
            severity=RuleSeverity.HIGH,
            text="Revenue growth declined by 20.0%.",
        )

        limitation = make_finding(
            rule_id="R010",
            category="Liquidity",
            severity=RuleSeverity.MEDIUM,
            text="Liquidity could not be evaluated.",
        )

        analysis = make_analysis(
            key_findings=[finding],
            limitations=[limitation],
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert "Liquidity could not be evaluated." not in prompt

    def test_build_returns_none_when_no_findings(self) -> None:
        analysis = make_analysis()

        prompt = ReportPromptBuilder().build(analysis)

        assert "DETERMINISTIC ASSESSMENT FINDINGS:" in prompt
        assert "None." in prompt

    def test_build_contains_grounding_instructions(self) -> None:
        finding = make_finding(
            rule_id="R001",
            category="Revenue",
            severity=RuleSeverity.HIGH,
            text="Revenue growth declined by 20.0%.",
        )

        analysis = make_analysis(
            key_findings=[finding],
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert "GROUNDING RULES:" in prompt
        assert "Do not invent facts" in prompt
        assert "Do not infer causality" in prompt

    def test_build_contains_narrative_guidance(self) -> None:
        finding = make_finding(
            rule_id="R001",
            category="Revenue",
            severity=RuleSeverity.HIGH,
            text="Revenue growth declined by 20.0%.",
        )

        analysis = make_analysis(
            key_findings=[finding],
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert "NARRATIVE GUIDANCE:" in prompt
        assert "Group related findings" in prompt
        assert "Synthesise multiple findings" in prompt

    def test_build_contains_output_contract(self) -> None:
        finding = make_finding(
            rule_id="R001",
            category="Revenue",
            severity=RuleSeverity.HIGH,
            text="Revenue growth declined by 20.0%.",
        )

        analysis = make_analysis(
            key_findings=[finding],
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert "OUTPUT REQUIREMENTS:" in prompt
        assert "Return only the executive narrative." in prompt
        assert "Do not include the assessment status." in prompt

    def test_build_preserves_numeric_values(self) -> None:
        findings = [
            make_finding(
                rule_id="R001",
                category="Revenue",
                severity=RuleSeverity.HIGH,
                text="Revenue growth declined by 20.0%.",
            ),
            make_finding(
                rule_id="R002",
                category="Profitability",
                severity=RuleSeverity.HIGH,
                text="EBITDA is negative at €-120,000.",
            ),
            make_finding(
                rule_id="R003",
                category="Profitability",
                severity=RuleSeverity.HIGH,
                text="Interest coverage ratio is -0.2x.",
            ),
            make_finding(
                rule_id="R004",
                category="Leverage",
                severity=RuleSeverity.HIGH,
                text="NFP to EBITDA is 7.0x.",
            ),
        ]

        analysis = make_analysis(
            key_findings=findings,
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert "20.0%" in prompt
        assert "€-120,000" in prompt
        assert "-0.2x" in prompt
        assert "7.0x" in prompt