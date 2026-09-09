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


@pytest.fixture
def generator():
    return DeterministicReportGenerator()


def make_analysis_finding(
    *,
    rule_id: str = "TEST_RULE",
    category: str = "test_category",
    severity: RuleSeverity = RuleSeverity.MEDIUM,
    text: str = "Test finding.",
) -> AnalysisFinding:
    return AnalysisFinding(
        rule_id=rule_id,
        category=category,
        severity=severity,
        text=text,
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
        key_findings=(key_findings if key_findings is not None else []),
        risk_factors=(risk_factors if risk_factors is not None else []),
        limitations=(limitations if limitations is not None else []),
    )


def findings_by_category_from_analysis(
    analysis: AssessmentAnalysis,
) -> list[ReportFindingGroup]:
    categories: dict[str, list[AnalysisFinding]] = {}

    for finding in analysis.key_findings:
        categories.setdefault(
            finding.category,
            [],
        ).append(finding)

    return [
        ReportFindingGroup(
            category=category,
            findings=findings,
        )
        for category, findings in categories.items()
    ]


def test_deterministic_report_generator_implements_contract(
    generator,
):
    assert isinstance(generator, ReportGenerator)


def test_deterministic_report_generator_preserves_analysis_data(
    generator,
):
    findings = [
        make_analysis_finding(
            rule_id=f"RULE_{index}",
            category=f"category_{index}",
            severity=severity,
            text=f"Finding {index}.",
        )
        for index, severity in enumerate(
            RuleSeverity,
            start=1,
        )
    ]

    limitations = [
        make_analysis_finding(
            rule_id=f"LIMITATION_{index}",
            category=f"category_{index}",
            severity=severity,
            text=f"Limitation {index}.",
        )
        for index, severity in enumerate(
            RuleSeverity,
            start=1,
        )
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
    assert report.findings_by_category == (findings_by_category_from_analysis(analysis))
    assert report.limitations == analysis.limitations


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
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
    assert report.executive_summary


def test_deterministic_report_generator_generates_distinct_summary_per_status(
    generator,
):
    summaries = {
        status: generator.generate(
            make_analysis(status=status),
        ).executive_summary
        for status in AssessmentStatus
    }

    assert len(summaries) == len(AssessmentStatus)
    assert len(set(summaries.values())) == len(AssessmentStatus)


def test_deterministic_report_generator_groups_findings_by_category(
    generator,
):
    findings = [
        make_analysis_finding(
            rule_id=f"RULE_{index}",
            category=category,
            severity=RuleSeverity.MEDIUM,
            text=f"Finding {index}.",
        )
        for index, category in enumerate(
            (
                "category_a",
                "category_b",
                "category_b",
                "category_c",
            ),
            start=1,
        )
    ]

    analysis = make_analysis(
        status=AssessmentStatus.ATTENTION,
        key_findings=findings,
    )

    report = generator.generate(analysis)

    assert report.findings_by_category == (findings_by_category_from_analysis(analysis))


def test_deterministic_report_generator_preserves_arbitrary_content(
    generator,
):
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
        ),
    ]

    limitations = [
        make_analysis_finding(
            rule_id="ARBITRARY_LIMITATION",
            category="arbitrary_limitation_category",
            severity=RuleSeverity.MEDIUM,
            text="Arbitrary limitation.",
        ),
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
    assert report.findings_by_category == (findings_by_category_from_analysis(analysis))
    assert report.limitations == analysis.limitations
