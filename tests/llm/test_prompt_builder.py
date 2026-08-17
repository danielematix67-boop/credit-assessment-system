import pytest

from src.llm.prompt_builder import ReportPromptBuilder
from src.llm.prompt_template import ReportPromptTemplate
from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.rules.base.severity import RuleSeverity


# ============================================================
# Fixtures / Factories
# ============================================================


def make_analysis_finding(
    *,
    rule_id: str = "TEST_RULE",
    category: str = "Test Category",
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
        key_findings=(
            key_findings
            if key_findings is not None
            else []
        ),
        risk_factors=(
            risk_factors
            if risk_factors is not None
            else []
        ),
        limitations=(
            limitations
            if limitations is not None
            else []
        ),
    )


@pytest.fixture
def analysis() -> AssessmentAnalysis:
    findings = [
        make_analysis_finding(
            rule_id=f"RULE_{index}",
            category=category,
            severity=severity,
            text=f"Finding {index}.",
        )
        for index, (category, severity) in enumerate(
            [
                ("Revenue", RuleSeverity.MEDIUM),
                ("Profitability", RuleSeverity.HIGH),
                ("Profitability", RuleSeverity.MEDIUM),
                ("Leverage", RuleSeverity.HIGH),
            ],
            start=1,
        )
    ]

    risk_factors = [
        finding
        for finding in findings
        if finding.severity == RuleSeverity.HIGH
    ]

    limitations = [
        make_analysis_finding(
            rule_id=f"LIMITATION_{index}",
            category="Limitation Category",
            severity=RuleSeverity.MEDIUM,
            text=f"Limitation {index}.",
        )
        for index in range(1, 3)
    ]

    return make_analysis(
        key_findings=findings,
        risk_factors=risk_factors,
        limitations=limitations,
    )


@pytest.fixture
def builder() -> ReportPromptBuilder:
    return ReportPromptBuilder()


# ============================================================
# Helpers
# ============================================================


def all_template_sections(
    template: ReportPromptTemplate,
) -> list[str]:
    """
    Return all static sections composing the default prompt template.

    The prompt contains only instructions relevant to the
    LLM-generated executive narrative.
    """

    return [
        template.ROLE,
        template.ARCHITECTURAL_BOUNDARY,
        template.SAFETY_CONSTRAINTS,
        template.SEMANTIC_DISTINCTION,
        template.NARRATIVE_GUIDANCE,
        template.OUTPUT_CONTRACT,
    ]


def all_findings(
    analysis: AssessmentAnalysis,
) -> list[AnalysisFinding]:
    return (
        analysis.key_findings
        + analysis.risk_factors
    )


def assert_finding_in_prompt(
    prompt: str,
    finding: AnalysisFinding,
) -> None:
    """
    Verify that all semantic information required to describe
    a deterministic finding is preserved in the prompt.
    """

    assert finding.rule_id in prompt
    assert finding.category in prompt
    assert finding.severity.value in prompt
    assert finding.text in prompt


# ============================================================
# Builder initialization
# ============================================================


def test_prompt_builder_uses_default_template():
    builder = ReportPromptBuilder()

    assert isinstance(
        builder.template,
        ReportPromptTemplate,
    )


def test_prompt_builder_accepts_custom_template():
    template = CustomReportPromptTemplate()

    builder = ReportPromptBuilder(
        template=template,
    )

    assert builder.template is template


# ============================================================
# Basic prompt construction
# ============================================================


def test_prompt_builder_returns_non_empty_string(
    builder,
    analysis,
):
    prompt = builder.build(analysis)

    assert isinstance(prompt, str)
    assert prompt.strip()


def test_prompt_builder_contains_all_template_sections(
    builder,
    analysis,
):
    prompt = builder.build(analysis)

    for section in all_template_sections(
        builder.template,
    ):
        assert section in prompt


def test_prompt_builder_preserves_template_section_order(
    builder,
    analysis,
):
    prompt = builder.build(analysis)

    sections = [
        builder.template.ROLE,
        builder.template.ARCHITECTURAL_BOUNDARY,
        builder.template.SAFETY_CONSTRAINTS,
        builder.template.SEMANTIC_DISTINCTION,
        builder.template.NARRATIVE_GUIDANCE,
        builder.template.OUTPUT_CONTRACT,
    ]

    positions = [
        prompt.index(section)
        for section in sections
    ]

    assert positions == sorted(positions)

# ============================================================
# Deterministic assessment input
# ============================================================


def test_prompt_builder_contains_dynamic_assessment_sections(
    builder,
    analysis,
):
    prompt = builder.build(analysis).lower()

    expected_sections = [
        "key findings",
        "risk factors",
    ]

    assert all(
        section in prompt
        for section in expected_sections
    )

def test_prompt_builder_excludes_non_narrative_assessment_data(
    builder,
    analysis,
):
    prompt = builder.build(analysis)

    assert analysis.assessment_status.value not in prompt

    for limitation in analysis.limitations:
        assert limitation.rule_id not in prompt
        assert limitation.text not in prompt


def test_prompt_builder_does_not_include_assessment_status_as_input(
    builder,
    analysis,
):
    prompt = builder.build(analysis)

    assert "Assessment status:" not in prompt
    assert analysis.assessment_status.value not in prompt


@pytest.mark.parametrize(
    "status",
    list(AssessmentStatus),
)
def test_prompt_builder_does_not_serialize_assessment_status(
    builder,
    status,
):
    analysis = make_analysis(
        status=status,
    )

    prompt = builder.build(analysis)

    assert "Assessment status:" not in prompt
    assert status.value not in prompt


# ============================================================
# Finding serialization
# ============================================================


def test_prompt_builder_serializes_finding_metadata(
    builder,
):
    finding = make_analysis_finding(
        rule_id="CUSTOM_RULE",
        category="Custom Category",
        severity=RuleSeverity.HIGH,
        text="A custom deterministic finding.",
    )

    analysis = make_analysis(
        key_findings=[finding],
    )

    prompt = builder.build(analysis)

    assert_finding_in_prompt(
        prompt,
        finding,
    )


def test_prompt_builder_serializes_all_analysis_findings(
    builder,
    analysis,
):
    prompt = builder.build(analysis)

    for finding in all_findings(analysis):
        assert_finding_in_prompt(
            prompt,
            finding,
        )


def test_prompt_builder_does_not_serialize_limitations(
    builder,
    analysis,
):
    prompt = builder.build(analysis)

    for limitation in analysis.limitations:
        assert limitation.rule_id not in prompt
        assert limitation.category not in prompt
        assert limitation.text not in prompt


def test_prompt_builder_serializes_arbitrary_number_of_findings(
    builder,
):
    findings = [
        make_analysis_finding(
            rule_id=f"DYNAMIC_RULE_{index}",
            category=f"Dynamic Category {index}",
            severity=RuleSeverity.MEDIUM,
            text=f"Dynamic finding {index}.",
        )
        for index in range(1, 11)
    ]

    analysis = make_analysis(
        key_findings=findings,
    )

    prompt = builder.build(analysis)

    for finding in findings:
        assert_finding_in_prompt(
            prompt,
            finding,
        )


def test_prompt_builder_preserves_finding_order(
    builder,
):
    findings = [
        make_analysis_finding(
            rule_id=f"ORDER_{index}",
            text=f"Ordered finding {index}.",
        )
        for index in range(1, 4)
    ]

    prompt = builder.build(
        make_analysis(
            key_findings=findings,
        ),
    )

    positions = [
        prompt.index(finding.rule_id)
        for finding in findings
    ]

    assert positions == sorted(positions)


# ============================================================
# Finding collections
# ============================================================


@pytest.mark.parametrize(
    "field_name",
    [
        "key_findings",
        "risk_factors",
    ],
)
def test_prompt_builder_serializes_each_finding_collection(
    builder,
    field_name,
):
    finding = make_analysis_finding(
        rule_id=f"{field_name.upper()}_RULE",
        category=f"{field_name.title()} Category",
        severity=RuleSeverity.HIGH,
        text=f"Finding belonging to {field_name}.",
    )

    analysis = make_analysis(
        **{
            field_name: [finding],
        },
    )

    prompt = builder.build(analysis)

    assert_finding_in_prompt(
        prompt,
        finding,
    )


def test_prompt_builder_keeps_collections_semantically_separated(
    builder,
):
    key_finding = make_analysis_finding(
        rule_id="KEY_RULE",
        text="Key finding.",
    )

    risk_finding = make_analysis_finding(
        rule_id="RISK_RULE",
        text="Risk factor.",
    )

    limitation = make_analysis_finding(
        rule_id="LIMITATION_RULE",
        text="Limitation.",
    )

    analysis = make_analysis(
        key_findings=[key_finding],
        risk_factors=[risk_finding],
        limitations=[limitation],
    )

    prompt = builder.build(analysis)

    key_position = prompt.index("Key findings:")
    risk_position = prompt.index("Risk factors:")

    assert key_position < risk_position

    # Limitations must remain outside the LLM prompt.
    assert "Limitations:" not in prompt
    assert limitation.rule_id not in prompt


# ============================================================
# Empty collections
# ============================================================


@pytest.mark.parametrize(
    "field_name",
    [
        "key_findings",
        "risk_factors",
    ],
)
def test_prompt_builder_represents_empty_collection_as_none(
    builder,
    field_name,
):
    analysis = make_analysis(
        **{
            field_name: [],
        },
    )

    prompt = builder.build(analysis)

    section_label = {
        "key_findings": "Key findings:",
        "risk_factors": "Risk factors:",
    }[field_name]

    section_position = prompt.index(
        section_label,
    )

    none_position = prompt.index(
        "None.",
        section_position,
    )

    assert none_position > section_position


def test_prompt_builder_supports_empty_analysis(
    builder,
):
    analysis = make_analysis()

    prompt = builder.build(analysis)

    assert prompt.strip()

    # Only the two collections sent to the LLM are represented.
    assert prompt.count("None.") >= 2

    # Status and limitations are not part of the prompt.
    assert "Assessment status:" not in prompt
    assert "Limitations:" not in prompt


# ============================================================
# Dynamic / non-hard-coded behaviour
# ============================================================


def test_prompt_builder_supports_arbitrary_categories(
    builder,
):
    findings = [
        make_analysis_finding(
            rule_id="RULE_A",
            category="Completely New Category",
            text="Finding from category A.",
        ),
        make_analysis_finding(
            rule_id="RULE_B",
            category="Another Previously Unknown Category",
            text="Finding from category B.",
        ),
    ]

    prompt = builder.build(
        make_analysis(
            key_findings=findings,
        ),
    )

    for finding in findings:
        assert_finding_in_prompt(
            prompt,
            finding,
        )


def test_prompt_builder_supports_arbitrary_rule_ids(
    builder,
):
    finding = make_analysis_finding(
        rule_id="RULE_THAT_DID_NOT_EXIST_BEFORE",
    )

    prompt = builder.build(
        make_analysis(
            key_findings=[finding],
        ),
    )

    assert finding.rule_id in prompt


@pytest.mark.parametrize(
    "severity",
    list(RuleSeverity),
)
def test_prompt_builder_supports_all_severity_values(
    builder,
    severity,
):
    finding = make_analysis_finding(
        severity=severity,
    )

    prompt = builder.build(
        make_analysis(
            key_findings=[finding],
        ),
    )

    assert severity.value in prompt


# ============================================================
# Finding text integrity
# ============================================================


@pytest.mark.parametrize(
    "text",
    [
        "Revenue declined by 15.2%.",
        "EBITDA remains negative.",
        "Liquidity data is unavailable.",
        "Special characters: %, /, -, :, (, ).",
        "Text containing multiple words and punctuation.",
    ],
)
def test_prompt_builder_preserves_finding_text(
    builder,
    text,
):
    finding = make_analysis_finding(
        text=text,
    )

    prompt = builder.build(
        make_analysis(
            key_findings=[finding],
        ),
    )

    assert finding.text in prompt


# ============================================================
# Deterministic data integrity
# ============================================================


def test_prompt_builder_does_not_modify_analysis(
    builder,
    analysis,
):
    original_key_findings = list(
        analysis.key_findings,
    )
    original_risk_factors = list(
        analysis.risk_factors,
    )
    original_limitations = list(
        analysis.limitations,
    )
    original_status = analysis.assessment_status

    builder.build(analysis)

    assert analysis.key_findings == original_key_findings
    assert analysis.risk_factors == original_risk_factors
    assert analysis.limitations == original_limitations
    assert analysis.assessment_status == original_status


# ============================================================
# Template isolation
# ============================================================


def test_prompt_builder_does_not_modify_template(
    analysis,
):
    template = ReportPromptTemplate()

    original_sections = all_template_sections(
        template,
    )

    builder = ReportPromptBuilder(
        template=template,
    )

    builder.build(analysis)

    current_sections = all_template_sections(
        template,
    )

    assert current_sections == original_sections


# ============================================================
# Custom template behaviour
# ============================================================


class CustomReportPromptTemplate:
    """
    Minimal custom template implementing the render contract
    required by ReportPromptBuilder.

    The builder must not depend on the concrete
    ReportPromptTemplate implementation.
    """

    def render(
        self,
        *,
        key_findings: str,
        risk_factors: str,
    ) -> str:
        return "\n".join(
            [
                "CUSTOM TEMPLATE",
                f"KEY_FINDINGS={key_findings}",
                f"RISK_FACTORS={risk_factors}",
            ],
        )


def test_prompt_builder_uses_custom_template():
    template = CustomReportPromptTemplate()

    builder = ReportPromptBuilder(
        template=template,
    )

    finding = make_analysis_finding(
        rule_id="CUSTOM_RULE",
        category="Custom Category",
        severity=RuleSeverity.HIGH,
        text="Custom finding.",
    )

    analysis = make_analysis(
        key_findings=[finding],
    )

    prompt = builder.build(analysis)

    assert "CUSTOM TEMPLATE" in prompt

    assert finding.rule_id in prompt
    assert finding.category in prompt
    assert finding.severity.value in prompt
    assert finding.text in prompt


def test_prompt_builder_delegates_rendering_to_custom_template():
    template = CustomReportPromptTemplate()

    builder = ReportPromptBuilder(
        template=template,
    )

    analysis = make_analysis()

    prompt = builder.build(analysis)

    assert prompt.startswith(
        "CUSTOM TEMPLATE",
    )

    assert "KEY_FINDINGS=None." in prompt
    assert "RISK_FACTORS=None." in prompt


# ============================================================
# Prompt semantic contract
# ============================================================


def test_prompt_builder_preserves_deterministic_source_of_truth(
    builder,
    analysis,
):
    prompt = builder.build(analysis).lower()

    concepts = [
        "deterministic",
        "source of truth",
        "assessment",
    ]

    assert all(
        concept in prompt
        for concept in concepts
    )


def test_prompt_builder_preserves_architectural_boundary(
    builder,
    analysis,
):
    prompt = builder.build(analysis).lower()

    concepts = [
        "do not reassess",
        "do not override",
        "credit decision",
        "do not modify",
    ]

    assert all(
        concept in prompt
        for concept in concepts
    )


def test_prompt_builder_preserves_grounding_constraints(
    builder,
    analysis,
):
    prompt = builder.build(analysis).lower()

    concepts = [
        "information provided",
        "do not invent",
        "do not introduce",
    ]

    assert all(
        concept in prompt
        for concept in concepts
    )


def test_prompt_builder_restricts_threshold_disclosure(
    builder,
    analysis,
):
    prompt = builder.build(analysis).lower()

    assert "threshold" in prompt

    disclosure_restrictions = (
        "do not disclose",
        "do not mention",
        "do not reproduce",
    )

    assert any(
        restriction in prompt
        for restriction in disclosure_restrictions
    )

def test_prompt_builder_excludes_assessment_status(
    builder,
    analysis,
):
    prompt = builder.build(analysis)

    assert analysis.assessment_status.value not in prompt


def test_prompt_builder_does_not_pass_status_value_to_llm(
    builder,
):
    for status in AssessmentStatus:
        analysis = make_analysis(
            status=status,
        )

        prompt = builder.build(analysis)

        assert status.value not in prompt


def test_prompt_builder_does_not_pass_limitations_to_llm(
    builder,
):
    limitation = make_analysis_finding(
        rule_id="SECRET_LIMITATION",
        category="Missing Data",
        severity=RuleSeverity.HIGH,
        text="This information is unavailable.",
    )

    analysis = make_analysis(
        limitations=[limitation],
    )

    prompt = builder.build(analysis)

    assert limitation.rule_id not in prompt
    assert limitation.category not in prompt
    assert limitation.severity.value not in prompt
    assert limitation.text not in prompt


def test_prompt_builder_restricts_unsupported_interpretation(
    builder,
    analysis,
):
    prompt = builder.build(analysis).lower()

    concepts = [
        "do not infer",
        "do not introduce",
        "do not change the meaning",
    ]

    assert all(
        concept in prompt
        for concept in concepts
    )


def test_prompt_builder_restricts_unsupported_causality(
    builder,
    analysis,
):
    prompt = builder.build(analysis).lower()

    assert "causality" in prompt
    assert "do not infer" in prompt


def test_prompt_builder_restricts_unsupported_trends(
    builder,
    analysis,
):
    prompt = builder.build(analysis).lower()

    assert "trend" in prompt
    assert "do not infer" in prompt


def test_prompt_builder_restricts_unsupported_business_implications(
    builder,
    analysis,
):
    prompt = builder.build(analysis).lower()

    concepts = [
        "business implications",
        "do not infer",
    ]

    assert all(
        concept in prompt
        for concept in concepts
    )


def test_prompt_builder_requires_narrative_only_output(
    builder,
    analysis,
):
    prompt = builder.build(analysis).lower()

    concepts = [
        "generate only the executive narrative",
        "do not add headings",
        "do not add bullet points",
        "do not add recommendations",
    ]

    assert all(
        concept in prompt
        for concept in concepts
    )

def test_prompt_builder_excludes_status_and_limitations(
    builder,
    analysis,
):
    prompt = builder.build(analysis)

    # Assessment status must remain outside the LLM prompt.
    assert analysis.assessment_status.value not in prompt

    # Limitations must remain outside the LLM prompt.
    for limitation in analysis.limitations:
        assert limitation.rule_id not in prompt
        assert limitation.text not in prompt