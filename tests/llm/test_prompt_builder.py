from src.llm.prompt_builder import ReportPromptBuilder
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.customer_profile_analysis import CustomerProfileAnalysis
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus


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
    customer_profile: CustomerProfileAnalysis | None = None,
    material_customer_profile: CustomerProfileAnalysis | None = None,
) -> AssessmentAnalysis:
    return AssessmentAnalysis(
        position_id="TEST-001",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=key_findings or [],
        risk_factors=[],
        limitations=[],
        rule_evidence=rule_evidence or [],
        customer_profile=customer_profile,
        material_customer_profile=material_customer_profile,
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
        assert "REQUIRED CATEGORY ORDER:" in prompt
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

    def test_build_formats_structured_customer_profile_context(self) -> None:
        profile = CustomerProfileAnalysis(
            general_information="The company operates in manufacturing.",
            risk_profile="The EWS Score is LIGHT_RED.",
            relationship_context="The banking relationship is two years.",
            relevant_events="A previous restructuring is reported.",
        )
        finding = make_finding(
            "CP001",
            "Customer Profile",
            RuleSeverity.MEDIUM,
            "Customer profile rule finding.",
        )
        analysis = make_analysis(
            key_findings=[finding],
            customer_profile=profile,
        )

        prompt = ReportPromptBuilder().build(analysis)

        assert "General Information:" in prompt
        assert "Risk Profile & Predictiveness:" in prompt
        assert "Relationship & Counterparty Context:" in prompt
        assert "Relevant Events:" in prompt
        assert "The EWS Score is LIGHT_RED." in prompt
        assert "Customer profile rule finding." in prompt

    def test_build_orders_financial_findings_by_narrative_theme(self) -> None:
        findings = [
            make_finding(
                "R010",
                "working_capital",
                RuleSeverity.MEDIUM,
                "Trade payables are increasing.",
            ),
            make_finding(
                "R004",
                "leverage",
                RuleSeverity.HIGH,
                "Leverage is elevated.",
            ),
            make_finding(
                "R001",
                "revenue",
                RuleSeverity.HIGH,
                "Revenue growth deteriorated.",
            ),
            make_finding(
                "R006",
                "profitability_quality",
                RuleSeverity.MEDIUM,
                "Earnings quality is weak.",
            ),
        ]
        findings = [
            AnalysisFinding(
                rule_id=finding.rule_id,
                category=finding.category,
                assessment_area="Financial Analysis",
                severity=finding.severity,
                text=finding.text,
            )
            for finding in findings
        ]

        prompt = ReportPromptBuilder().build(make_analysis(key_findings=findings))

        assert prompt.index("Revenue growth deteriorated.") < prompt.index(
            "Earnings quality is weak."
        )
        assert prompt.index("Earnings quality is weak.") < prompt.index(
            "Trade payables are increasing."
        )
        assert prompt.index("Trade payables are increasing.") < prompt.index(
            "Leverage is elevated."
        )
        assert "Narrative theme: Revenue and operating profitability" in prompt
        assert "Narrative theme: Earnings quality and operating structure" in prompt
        assert "Narrative theme: Working capital and cash conversion" in prompt
        assert "Narrative theme: Leverage and funding structure" in prompt

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
        assert "Return exactly four labeled sections" in prompt
        assert "Always include the Debt Sustainability section" in prompt
        assert "End immediately after the Debt Sustainability paragraph" in prompt
        assert "No deterministic anomalies are present for this area." in prompt
        assert "CUSTOMER PROFILE IS A MANDATORY EXCEPTION TO BREVITY" in prompt
        assert "every non-empty subsection" in prompt
        assert "lack of a rule trigger" in prompt
        assert (
            "company background, sector, operations, ownership, management, facilities"
            in prompt
        )
        assert "Do not replace detailed context with a generic risk-profile summary." in prompt
        assert "REWRITE, DO NOT TRANSCRIBE" in prompt
        assert "Re-express their meaning in natural, fluent and varied professional prose." in prompt
        assert "the explanatory wording around that label may be paraphrased." in prompt
        assert "Do not merge distinct signals" in prompt
        assert "SYNTHESIZE RELATED CONCEPTS" in prompt
        assert "Keep each indicator label verbatim" in prompt

    def test_build_returns_none_when_no_findings(self) -> None:
        prompt = ReportPromptBuilder().build(make_analysis())

        assert "ANALYSIS FINDINGS:" in prompt
        assert "No deterministic anomalies are present for this area." in prompt


def test_build_excludes_non_triggered_rules_but_keeps_not_evaluable_evidence() -> None:
    not_triggered = AnalysisFinding(
        rule_id="R001",
        category="Financial Analysis",
        severity=RuleSeverity.LOW,
        text="Revenue growth is stable.",
        status=RuleStatus.NOT_TRIGGERED,
        assessment_area="Financial Analysis",
        indicator="Revenue growth",
    )
    not_evaluable = AnalysisFinding(
        rule_id="R002",
        category="Financial Analysis",
        severity=RuleSeverity.MEDIUM,
        text="Interest coverage: no sufficiently reliable value is available.",
        status=RuleStatus.NOT_EVALUABLE,
        assessment_area="Financial Analysis",
        indicator="Interest coverage",
    )
    triggered = AnalysisFinding(
        rule_id="R003",
        category="Financial Analysis",
        severity=RuleSeverity.HIGH,
        text="EBITDA is negative.",
        status=RuleStatus.TRIGGERED,
        assessment_area="Financial Analysis",
        indicator="EBITDA",
    )

    prompt = ReportPromptBuilder().build(
        make_analysis(rule_evidence=[not_triggered, not_evaluable, triggered])
    )

    assert "Revenue growth is stable." not in prompt
    assert "Interest coverage: no sufficiently reliable value is available." in prompt
    assert "EBITDA is negative." in prompt
    assert "[NOT EVALUABLE]" in prompt
