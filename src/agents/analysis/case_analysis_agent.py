from collections.abc import Callable

from src.models.analysis_finding import AnalysisFinding
from src.models.assessment_analysis import AssessmentAnalysis
from src.models.assessment_status import AssessmentStatus
from src.models.credit_assessment_case import CreditAssessmentCase
from src.models.customer_profile_analysis import CustomerProfileAnalysis
from src.models.final_assessment import FinalAssessment
from src.rules.base.severity import RuleSeverity
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult
from src.services.customer_profile_materiality_policy import (
    CustomerProfileMaterialityPolicy,
)


class CaseAnalysisAgent:
    """Adapt deterministic case evidence into the reporting analysis contract."""

    def run(self, case: CreditAssessmentCase) -> AssessmentAnalysis:
        final_assessment = case.final_assessment or self._require_final_assessment(case)
        rule_evidence: list[AnalysisFinding] = []
        key_findings: list[AnalysisFinding] = []
        risk_factors: list[AnalysisFinding] = []
        limitations: list[AnalysisFinding] = []
        customer_profile_analysis: CustomerProfileAnalysis | None = None
        material_customer_profile_analysis: CustomerProfileAnalysis | None = None

        if case.customer_profile.context:
            summary = self._profile_summary(case.customer_profile.context)
            if summary:
                customer_profile_analysis = self._customer_profile_analysis(summary)
                material_fields = CustomerProfileMaterialityPolicy.material_fields(
                    case.customer_profile.context
                )
                material_summary = self._profile_summary(
                    case.customer_profile.context,
                    fields=material_fields,
                )
                if material_summary:
                    material_customer_profile_analysis = self._customer_profile_analysis(
                        material_summary
                    )

        for section in case.sections:
            triggered_text_by_rule = {
                finding.result.rule_id: finding.comment.text
                for finding in section.findings
            }
            section_rule_evidence = [
                self._rule_evidence_finding(
                    result,
                    assessment_area=section.name,
                    triggered_text=triggered_text_by_rule.get(result.rule_id),
                )
                for result in section.evidence
            ]

            if not section_rule_evidence:
                section_rule_evidence = [
                    AnalysisFinding(
                        rule_id=finding.result.rule_id,
                        category=finding.result.category,
                        severity=finding.result.severity,
                        text=finding.comment.text,
                        status=finding.result.status,
                        assessment_area=section.name,
                        value=finding.result.value,
                        indicator=finding.result.indicator,
                    )
                    for finding in section.findings
                ]

            rule_evidence.extend(section_rule_evidence)

            for finding in section.findings:
                evidence = next(
                    evidence
                    for evidence in section_rule_evidence
                    if evidence.rule_id == finding.result.rule_id
                )
                key_findings.append(evidence)

                if (
                    finding.result.status == RuleStatus.TRIGGERED
                    and finding.result.severity == RuleSeverity.HIGH
                ):
                    risk_factors.append(evidence)

            for limitation in section.limitations:
                limitations.append(
                    AnalysisFinding(
                        rule_id=f"SECTION:{section.name}",
                        category=section.name,
                        severity=RuleSeverity.MEDIUM,
                        text=limitation,
                        assessment_area=section.name,
                    )
                )

        for limitation in final_assessment.limitations:
            limitations.append(
                AnalysisFinding(
                    rule_id="FINAL",
                    category="Final Assessment",
                    severity=RuleSeverity.MEDIUM,
                    text=limitation,
                )
            )

        return AssessmentAnalysis(
            position_id=case.position.position_id,
            assessment_status=self._to_assessment_status(final_assessment),
            key_findings=key_findings,
            risk_factors=risk_factors,
            limitations=limitations,
            rule_evidence=rule_evidence,
            customer_profile=customer_profile_analysis,
            material_customer_profile=material_customer_profile_analysis,
        )

    @staticmethod
    def _rule_evidence_finding(
        result: RuleResult,
        *,
        assessment_area: str,
        triggered_text: str | None = None,
    ) -> AnalysisFinding:
        """Expose every deterministic rule result in reporting-safe language."""
        if result.status == RuleStatus.TRIGGERED:
            text = triggered_text or result.indicator or result.rule_name
        elif result.status == RuleStatus.NOT_TRIGGERED:
            if result.reason:
                text = result.reason
            else:
                value = CaseAnalysisAgent._format_value(result.value)
                indicator = result.indicator or result.rule_name
                text = (
                    f"{indicator} is {value}; the observed value does not meet "
                    "the deterministic trigger condition."
                )
        else:
            indicator = result.indicator or result.rule_name
            text = (
                f"{indicator}: no sufficiently reliable value is available; "
                "the rule cannot be evaluated."
            )

        return AnalysisFinding(
            rule_id=result.rule_id,
            category=result.category,
            severity=result.severity,
            text=text,
            status=result.status,
            assessment_area=assessment_area,
            value=result.value,
            indicator=result.indicator,
        )

    @staticmethod
    def _format_value(value: object) -> str:
        if isinstance(value, float):
            return f"{value:g}"
        return str(value)

    @staticmethod
    def _require_final_assessment(case: CreditAssessmentCase) -> FinalAssessment:
        from src.services.final_assessment_service import FinalAssessmentService

        return FinalAssessmentService().assess(case)

    @staticmethod
    def _to_assessment_status(final_assessment: FinalAssessment) -> AssessmentStatus:
        return AssessmentStatus(final_assessment.status.value)

    @staticmethod
    def _customer_profile_analysis(summary: str) -> CustomerProfileAnalysis:
        """Map the structured profile narrative into four reporting sections."""
        import re

        headings = (
            "General Information",
            "Risk Profile & Predictiveness",
            "Relationship & Counterparty Context",
            "Relevant Events",
        )
        pattern = r"(?=^\*\*(?:" + "|".join(re.escape(h) for h in headings) + r")\*\*\s*$)"
        matches = list(re.finditer(pattern, summary, flags=re.MULTILINE))
        sections: list[str] = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(summary)
            sections.append(summary[match.start():end].strip())
        padded = (sections + [""] * 4)[:4]
        return CustomerProfileAnalysis(
            general_information=padded[0],
            risk_profile=padded[1],
            relationship_context=padded[2],
            relevant_events=padded[3],
        )

    @staticmethod
    def _profile_summary(
        profile: dict[str, object],
        fields: set[str] | None = None,
    ) -> str:
        """Build a readable, structured Customer Profile with human-readable bullets."""
        def included(key: str) -> bool:
            item = profile.get(key)
            return item not in (None, "", [], {}) and (fields is None or key in fields)

        def text(item: object) -> str:
            if isinstance(item, bool):
                return "Yes" if item else "No"
            if isinstance(item, list):
                return ", ".join(str(entry) for entry in item)
            return str(item)

        def bullet(
            label: str,
            key: str,
            transform: Callable[[object], str] | None = None,
        ) -> str | None:
            if not included(key):
                return None
            item = profile[key]
            rendered = transform(item) if transform else text(item)
            return f"- **{label}:** {rendered}"

        def section(
            title: str,
            lines: list[str | None],
            introduction: str | None = None,
        ) -> str:
            populated = [line for line in lines if line]
            body = [f"**{title}**"]
            if introduction:
                body.extend(("", introduction))
            if populated:
                body.extend(("", "\n\n".join(populated)))
            elif not introduction:
                body.extend(("", "No additional information available."))
            return "\n".join(body)

        def records(key: str) -> list[object]:
            item = profile.get(key)
            return item if isinstance(item, list) else []

        company_name = profile.get("company_name")
        introduction_parts: list[str] = []
        if isinstance(company_name, str) and company_name.strip():
            introduction_parts.append(f"{company_name.strip()} is the customer under assessment.")
        sector = profile.get("sector")
        if isinstance(sector, str) and sector.strip():
            introduction_parts.append(f"The company operates in the {sector.strip()} sector.")
        founding_year = profile.get("founding_year")
        if founding_year not in (None, ""):
            introduction_parts.append(f"It was established in {founding_year}.")
        general = section("General Information", [
            bullet("Customer", "company_name"),
            bullet("Sector", "sector"),
            bullet("Company size", "size_class"),
            bullet("Geography", "geography"),
            bullet("Business activities", "operations"),
            bullet("Established", "founding_year"),
            bullet("Operating history", "business_history_years",
                   lambda v: f"{v} year" if v == 1 else f"{v} years"),
        ], " ".join(introduction_parts) or "General customer information is available as summarised below.")
        risk = section("Risk Profile & Predictiveness", [
            bullet("Minimum regulatory risk grade", "minimum_regulatory_risk_grade"),
            bullet("Previous risk grade", "previous_risk_grade"),
            bullet("Risk-grade change", "risk_grade_change"),
            bullet("Past-due positions", "past_due_count"),
            bullet("EWS Score class", "ews_score_class"),
            bullet("EWS notching", "ews_score_notching"),
            bullet("EWS variation", "ews_score_variation"),
            bullet("Active early-warning indicators", "active_ewis"),
            bullet("Rating", "rating"),
            bullet("Rating notching", "rating_notching"),
            bullet("Rating factors", "rating_influential_factors"),
            bullet("Rating modules", "rating_elementary_modules"),
            bullet("Probability of default (PD)", "pd"),
        ])

        relationship_lines = [
            bullet("Banking relationship", "relationship_years",
                   lambda v: f"{v} year" if v == 1 else f"{v} years"),
            bullet("Risk-group interdependence", "risk_group_interdependence"),
            bullet("Risk-group independence", "risk_group_independence"),
            bullet("Shareholders", "shareholders"),
            bullet("Shareholder roles", "shareholder_roles"),
            bullet("Management", "management_members"),
            bullet("Generational transition", "generational_transition"),
            bullet("Historical facilities", "historical_facilities"),
            bullet("Employment contract", "employment_contract_type"),
            bullet("Economic-family context", "economic_family_context"),
        ]
        shareholders = records("shareholder_details") if included("shareholder_details") else []
        if shareholders:
            relationship_lines.extend(("", "**Shareholding structure**", ""))
            relationship_lines.extend(f"- {entry}" for entry in shareholders)
        facilities = records("credit_facility_details") if included("credit_facility_details") else []
        if facilities:
            relationship_lines.extend(("", "**Credit facilities**", ""))
            relationship_lines.extend(f"- {entry}" for entry in facilities)
        relationship = section("Relationship & Counterparty Context", relationship_lines)

        event_lines = [
            bullet("Previous restructuring", "previous_restructuring"),
            bullet("Forborne exposure", "forborne"),
            bullet("Exit from forborne non-performing status", "forborne_non_performing_exit"),
            bullet("Cure period", "cure_period_days", lambda v: f"{v} days"),
            bullet("Monitoring period", "monitoring_period_days", lambda v: f"{v} days"),
            bullet("Probation period", "probation_period_days", lambda v: f"{v} days"),
            bullet("Protests", "protests"),
            bullet("Bankruptcies", "bankruptcies"),
            bullet("Litigation", "litigation"),
            bullet("Significant historical events", "significant_historical_events"),
        ]
        event_records = records("relevant_event_details") if included("relevant_event_details") else []
        if event_records:
            event_lines.extend(("", "**Recorded events**", ""))
            event_lines.extend(f"- {entry}" for entry in event_records)
        events = section("Relevant Events", event_lines)

        return "\n\n".join((general, risk, relationship, events))
