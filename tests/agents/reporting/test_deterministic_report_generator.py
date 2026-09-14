import pytest

from src.agents.reporting.deterministic_report_generator import (
    DeterministicReportGenerator,
)
from src.agents.reporting.report_generator import ReportGenerator
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.report import ReportFindingGroup
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus


@pytest.fixture
def generator():
    return DeterministicReportGenerator()


def make_analysis_finding(
    *,
    rule_id: str = "TEST_RULE",
    category: str = "test_category",
    severity: RuleSeverity = RuleSeverity.MEDIUM,
    text: str = "Test finding.",
    status: RuleStatus | None = RuleStatus.TRIGGERED,
) -> AnalysisFinding:
    return AnalysisFinding(
        rule_id=rule_id,
        category=category,
        severity=severity,
        text=text,
        status=status,
    )


def make_analysis(
    *,
    position_id: str = "TEST_POSITION",
    status: AssessmentStatus = AssessmentStatus.ATTENTION,
    key_findings: list[AnalysisFinding] | None = None,
    risk_factors: list[AnalysisFinding] | None = None,
    limitations: list[AnalysisFinding] | None = None,
) -> AssessmentAnalysis:
    return AssessmentAnalysis(
        position_id=position_id,
        assessment_status=status,
        key_findings=key_findings if key_findings is not None else [],
        risk_factors=risk_factors if risk_factors is not None else [],
        limitations=limitations if limitations is not None else [],
    )


def findings_by_category_from_analysis(
    analysis: AssessmentAnalysis,
) -> list[ReportFindingGroup]:
    categories: dict[str, list[AnalysisFinding]] = {}
    for finding in analysis.key_findings:
        categories.setdefault(finding.category, []).append(finding)
    return [
        ReportFindingGroup(category=category, findings=findings)
        for category, findings in categories.items()
    ]


def test_deterministic_report_generator_implements_contract(generator):
    assert isinstance(generator, ReportGenerator)


def test_deterministic_report_generator_preserves_analysis_data(generator):
    findings = [
        make_analysis_finding(
            rule_id=f"RULE_{index}",
            category=f"category_{index}",
            severity=severity,
            text=f"Finding {index}.",
        )
        for index, severity in enumerate(RuleSeverity, start=1)
    ]
    limitations = [
        make_analysis_finding(
            rule_id=f"LIMITATION_{index}",
            category=f"category_{index}",
            severity=severity,
            text=f"Limitation {index}.",
        )
        for index, severity in enumerate(RuleSeverity, start=1)
    ]
    analysis = make_analysis(
        position_id="CUSTOM_POSITION",
        status=AssessmentStatus.ATTENTION,
        key_findings=findings,
        limitations=limitations,
    )
    report = generator.generate(analysis)
    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.findings_by_category == findings_by_category_from_analysis(analysis)
    assert report.limitations == analysis.limitations


@pytest.mark.parametrize("status", list(AssessmentStatus))
def test_deterministic_report_generator_generates_summary_for_each_status(
    generator,
    status,
):
    analysis = make_analysis(status=status)
    report = generator.generate(analysis)
    assert report.position_id == analysis.position_id
    assert report.assessment_status == status
    assert report.findings_by_category == []
    assert report.limitations == []
    assert report.executive_summary == f"Assessment Status: {status.value.capitalize()}"


def test_deterministic_report_generator_status_is_authoritative_and_separate(generator):
    analysis = make_analysis(
        status=AssessmentStatus.CRITICAL,
        key_findings=[make_analysis_finding(text="EBITDA is negative at €-120,000.")],
    )
    report = generator.generate(analysis)
    assert report.executive_summary == (
        "Assessment Status: Critical\n\n"
        "EBITDA is negative at €-120,000."
    )
    assert report.executive_summary.count("Assessment Status:") == 1


def test_deterministic_fallback_uses_structured_status_not_text(generator):
    findings = [
        make_analysis_finding(
            rule_id="R001",
            category="Revenue",
            text="Revenue growth declined to -20.0%.",
            status=RuleStatus.TRIGGERED,
        ),
        make_analysis_finding(
            rule_id="R002",
            category="Revenue",
            text="Revenue growth is 5.0%; this wording contains no status cue.",
            status=RuleStatus.NOT_TRIGGERED,
        ),
        make_analysis_finding(
            rule_id="R003",
            category="Revenue",
            text="Revenue growth: no sufficiently reliable value is available.",
            status=RuleStatus.NOT_EVALUABLE,
        ),
    ]
    analysis = make_analysis(
        status=AssessmentStatus.ATTENTION,
        key_findings=findings,
    )
    report = generator.generate(analysis)
    assert "Revenue growth declined to -20.0%." in report.executive_summary
    assert "5.0%" not in report.executive_summary
    assert "no sufficiently reliable" not in report.executive_summary


def test_deterministic_fallback_classification_is_invariant_to_finding_wording(generator):
    original = make_analysis_finding(
        rule_id="R001",
        category="Revenue",
        text="Revenue growth declined to -20.0%.",
        status=RuleStatus.TRIGGERED,
    )
    rewritten = make_analysis_finding(
        rule_id="R001",
        category="Revenue",
        text="The observed revenue metric is materially below the reference level.",
        status=RuleStatus.TRIGGERED,
    )

    original_report = generator.generate(make_analysis(key_findings=[original]))
    rewritten_report = generator.generate(make_analysis(key_findings=[rewritten]))

    assert original_report.findings_by_category[0].findings[0].status == RuleStatus.TRIGGERED
    assert rewritten_report.findings_by_category[0].findings[0].status == RuleStatus.TRIGGERED
    assert rewritten_report.executive_summary.endswith(rewritten.text)


def test_deterministic_report_rejects_rule_evidence_without_status(generator):
    analysis = make_analysis(
        key_findings=[
            make_analysis_finding(
                rule_id="R001",
                category="Revenue",
                text="Revenue growth declined to -20.0%.",
                status=None,
            )
        ]
    )

    with pytest.raises(ValueError, match="Rule evidence requires a structured RuleStatus"):
        generator.generate(analysis)


def test_deterministic_report_allows_profile_summary_without_rule_status(generator):
    profile = make_analysis_finding(
        rule_id="PROFILE",
        category="Customer Profile",
        text="Company: Example S.p.A.",
        status=None,
    )
    report = generator.generate(make_analysis(key_findings=[profile]))

    assert "### Customer Profile" in report.executive_summary
    assert "Company: Example S.p.A." in report.executive_summary


def test_deterministic_fallback_keeps_all_findings_in_category_paragraphs(generator):
    findings = [
        make_analysis_finding(
            category="Revenue",
            text="Revenue growth declined to -20.0%.",
        ),
        make_analysis_finding(
            category="Profitability",
            text="EBITDA is negative at €-120,000.",
        ),
        make_analysis_finding(
            category="Profitability",
            text="Interest coverage ratio is -0.2x.",
        ),
        make_analysis_finding(
            category="Leverage",
            text="NFP to EBITDA stands at 7.0x.",
        ),
    ]
    analysis = make_analysis(
        status=AssessmentStatus.CRITICAL,
        key_findings=findings,
    )
    report = generator.generate(analysis)
    assert report.executive_summary == (
        "Assessment Status: Critical\n\n"
        "Revenue growth declined to -20.0%.\n\n"
        "EBITDA is negative at €-120,000. Interest coverage ratio is -0.2x.\n\n"
        "NFP to EBITDA stands at 7.0x."
    )


def test_deterministic_fallback_fixed_assessment_area_headings_follow_canonical_order(
    generator,
):
    findings = [
        make_analysis_finding(
            category="Debt Sustainability",
            text="DSCR remains weak.",
        ),
        make_analysis_finding(
            category="Behavioural Analysis",
            text="Payment delays increased.",
        ),
        make_analysis_finding(
            category="Customer Profile",
            text="Customer context.",
            rule_id="PROFILE",
            status=None,
        ),
        make_analysis_finding(
            category="Financial Analysis",
            text="Revenue declined.",
        ),
    ]
    report = generator.generate(make_analysis(key_findings=findings))

    assert report.executive_summary == (
        "Assessment Status: Attention\n\n"
        "### Customer Profile\n\nCustomer context.\n\n"
        "### Financial Analysis\n\nRevenue declined.\n\n"
        "### Behavioural Analysis\n\nPayment delays increased.\n\n"
        "### Debt Sustainability\n\nDSCR remains weak."
    )


def test_deterministic_report_generator_groups_findings_by_category(generator):
    findings = [
        make_analysis_finding(
            rule_id=f"RULE_{index}",
            category=category,
            severity=RuleSeverity.MEDIUM,
            text=f"Finding {index}.",
        )
        for index, category in enumerate(
            ("category_a", "category_b", "category_b", "category_c"),
            start=1,
        )
    ]
    analysis = make_analysis(status=AssessmentStatus.ATTENTION, key_findings=findings)
    report = generator.generate(analysis)
    assert report.findings_by_category == findings_by_category_from_analysis(analysis)


def test_deterministic_report_generator_preserves_arbitrary_content(generator):
    key_findings = [
        make_analysis_finding(
            rule_id="ARBITRARY_RULE_A",
            category="arbitrary_category_a",
            severity=RuleSeverity.LOW,
            text="Arbitrary finding A.",
        ),
        make_analysis_finding(
            rule_id="ARBITRARY_RULE_B",
            category="arbitrary_category_b",
            severity=RuleSeverity.HIGH,
            text="Arbitrary finding B.",
        ),
    ]
    risk_factors = [
        make_analysis_finding(
            rule_id="ARBITRARY_RISK",
            category="arbitrary_risk_category",
            severity=RuleSeverity.HIGH,
            text="Arbitrary risk.",
        )
    ]
    limitations = [
        make_analysis_finding(
            rule_id="ARBITRARY_LIMITATION",
            category="arbitrary_limitation_category",
            severity=RuleSeverity.MEDIUM,
            text="Arbitrary limitation.",
        )
    ]
    analysis = make_analysis(
        position_id="ARBITRARY_POSITION",
        status=AssessmentStatus.NORMAL,
        key_findings=key_findings,
        risk_factors=risk_factors,
        limitations=limitations,
    )
    report = generator.generate(analysis)
    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status
    assert report.findings_by_category == findings_by_category_from_analysis(analysis)
    assert report.limitations == analysis.limitations
