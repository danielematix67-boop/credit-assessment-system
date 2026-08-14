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


@pytest.fixture
def analysis():
    return AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=AssessmentStatus.CRITICAL,
        key_findings=[
            AnalysisFinding(
                rule_id="R001",
                category="revenue",
                severity=RuleSeverity.MEDIUM,
                text="Revenue deterioration detected.",
            ),
            AnalysisFinding(
                rule_id="R002",
                category="profitability",
                severity=RuleSeverity.HIGH,
                text="Negative EBITDA detected.",
            ),
            AnalysisFinding(
                rule_id="R003",
                category="profitability",
                severity=RuleSeverity.MEDIUM,
                text="EBITDA margin is below the acceptable threshold.",
            ),
        ],
        risk_factors=[
            AnalysisFinding(
                rule_id="R002",
                category="profitability",
                severity=RuleSeverity.HIGH,
                text="Negative EBITDA detected.",
            ),
        ],
        limitations=[
            AnalysisFinding(
                rule_id="R005",
                category="profitability",
                severity=RuleSeverity.MEDIUM,
                text="Interest expense to EBITDA could not be evaluated.",
            ),
        ],
    )


def findings_by_category_from_analysis(analysis):
    categories = {}

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
    analysis,
):
    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status

    assert report.findings_by_category == (
        findings_by_category_from_analysis(analysis)
    )

    assert report.limitations == analysis.limitations


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_deterministic_report_generator_generates_summary_for_each_status(
    generator,
    status,
):
    analysis = AssessmentAnalysis(
        position_id="TEST_POSITION",
        assessment_status=status,
        key_findings=[],
        risk_factors=[],
        limitations=[],
    )

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == status
    assert report.findings_by_category == []
    assert report.limitations == []
    assert report.executive_summary


def test_deterministic_report_generator_summary_depends_on_status(
    generator,
):
    summaries = {}

    for status in AssessmentStatus:
        analysis = AssessmentAnalysis(
            position_id="TEST_POSITION",
            assessment_status=status,
            key_findings=[],
            risk_factors=[],
            limitations=[],
        )

        report = generator.generate(analysis)
        summaries[status] = report.executive_summary

    assert len(set(summaries.values())) == len(AssessmentStatus)


def test_deterministic_report_generator_groups_findings_by_category(
    generator,
):
    analysis = AssessmentAnalysis(
        position_id="CUSTOM_POSITION",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            AnalysisFinding(
                rule_id="R001",
                category="revenue",
                severity=RuleSeverity.MEDIUM,
                text="Revenue declined.",
            ),
            AnalysisFinding(
                rule_id="R002",
                category="profitability",
                severity=RuleSeverity.HIGH,
                text="Negative EBITDA detected.",
            ),
            AnalysisFinding(
                rule_id="R003",
                category="profitability",
                severity=RuleSeverity.MEDIUM,
                text="EBITDA margin deteriorated.",
            ),
            AnalysisFinding(
                rule_id="R004",
                category="leverage",
                severity=RuleSeverity.HIGH,
                text="Leverage is elevated.",
            ),
        ],
        risk_factors=[],
        limitations=[],
    )

    report = generator.generate(analysis)

    assert report.findings_by_category == (
        findings_by_category_from_analysis(analysis)
    )


def test_deterministic_report_generator_preserves_custom_content(
    generator,
):
    analysis = AssessmentAnalysis(
        position_id="CUSTOM_POSITION",
        assessment_status=AssessmentStatus.ATTENTION,
        key_findings=[
            AnalysisFinding(
                rule_id="CUSTOM_REVENUE",
                category="revenue",
                severity=RuleSeverity.MEDIUM,
                text="CUSTOM FINDING",
            ),
            AnalysisFinding(
                rule_id="CUSTOM_PROFITABILITY",
                category="profitability",
                severity=RuleSeverity.HIGH,
                text="CUSTOM PROFITABILITY FINDING",
            ),
        ],
        risk_factors=[
            AnalysisFinding(
                rule_id="CUSTOM_RISK",
                category="leverage",
                severity=RuleSeverity.HIGH,
                text="CUSTOM RISK",
            ),
        ],
        limitations=[
            AnalysisFinding(
                rule_id="CUSTOM_LIMITATION",
                category="liquidity",
                severity=RuleSeverity.MEDIUM,
                text="CUSTOM LIMITATION",
            ),
        ],
    )

    report = generator.generate(analysis)

    assert report.position_id == analysis.position_id
    assert report.assessment_status == analysis.assessment_status

    assert report.findings_by_category == (
        findings_by_category_from_analysis(analysis)
    )

    assert report.limitations == analysis.limitations
