
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
            behavioural_context=dict(case.behavioural_analysis.context),
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
        """Build a readable prose narrative from customer-profile context."""
        def included(key: str) -> bool:
            item = profile.get(key)
            return item not in (None, "", [], {}) and (fields is None or key in fields)

        def value(key: str) -> str:
            item = profile[key]
            if isinstance(item, bool):
                return "yes" if item else "no"
            if isinstance(item, list):
                return ", ".join(str(entry) for entry in item)
            return str(item)

        def add(parts: list[str], key: str, phrase: str) -> None:
            if included(key):
                parts.append(phrase.format(value=value(key)))

        def section(title: str, prose: str) -> str:
            return f"**{title}**\n\n{prose.strip()}" if prose.strip() else (
                f"**{title}**\n\nNo additional information available."
            )

        # General information: introduce the company once and avoid repeating
        # the same company, sector and establishment year as labelled fields.
        general_parts: list[str] = []
        company = value("company_name") if included("company_name") else "The customer"
        opening = [company]
        if included("sector"):
            opening.append(f"operates in the {value('sector')} sector")
        if included("operations"):
            opening.append(f"with activities focused on {value('operations')}")
        general_sentence = " ".join(opening) + "."
        general_details: list[str] = []
        add(general_details, "size_class", "It is classified as a {value}.")
        add(general_details, "geography", "Its main geographical base is {value}.")
        add(general_details, "founding_year", "The company was established in {value}.")
        add(
            general_details,
            "business_history_years",
            "Its operating history spans {value} years.",
        )
        general_parts.append(general_sentence)
        general_parts.extend(general_details)
        general = section("General Information", " ".join(general_parts))

        # Risk profile: group related grades, EWS signals and rating information
        # into connected sentences instead of repeating "X is Y" field labels.
        risk_parts: list[str] = []
        if included("minimum_regulatory_risk_grade"):
            minimum_grade = value("minimum_regulatory_risk_grade")
            if included("previous_risk_grade"):
                previous_grade = value("previous_risk_grade")
                change = (
                    f", with a {value('risk_grade_change').lower()} trend"
                    if included("risk_grade_change")
                    else ""
                )
                risk_parts.append(
                    f"The minimum regulatory risk grade is {minimum_grade}, "
                    f"compared with {previous_grade} previously{change}."
                )
            else:
                risk_parts.append(f"The minimum regulatory risk grade is {minimum_grade}.")
        elif included("previous_risk_grade"):
            risk_parts.append(f"The previous risk grade was {value('previous_risk_grade')}.")

        if included("past_due_count"):
            risk_parts.append(f"The recorded number of past-due positions is {value('past_due_count')}.")
        ews_parts: list[str] = []
        add(ews_parts, "ews_score_class", "an EWS score class of {value}")
        add(ews_parts, "ews_score_notching", "EWS notching of {value}")
        add(ews_parts, "ews_score_variation", "an EWS variation of {value}")
        add(ews_parts, "active_ewis", "active early-warning indicators comprising {value}")
        if ews_parts:
            risk_parts.append("Early-warning information includes " + ", ".join(ews_parts) + ".")
        rating_parts: list[str] = []
        add(rating_parts, "rating", "a rating of {value}")
        add(rating_parts, "rating_notching", "rating notching of {value}")
        add(rating_parts, "pd", "a probability of default (PD) of {value}")
        add(rating_parts, "rating_influential_factors", "the following rating factors: {value}")
        add(rating_parts, "rating_elementary_modules", "rating modules covering {value}")
        if rating_parts:
            risk_parts.append("The rating assessment records " + ", ".join(rating_parts) + ".")
        risk = section("Risk Profile & Predictiveness", " ".join(risk_parts))

        # Relationship context: describe group links and ownership, then retain
        # all facility details without turning each attribute into a bullet.
        relationship_parts: list[str] = []
        # Risk-group interdependence/independence are intentionally excluded
        # from the narrative.
        add(relationship_parts, "relationship_years", "The banking relationship has lasted {value} years.")
        add(relationship_parts, "shareholders", "The shareholders are {value}.")
        add(relationship_parts, "shareholder_roles", "Shareholders' roles include {value}.")
        add(relationship_parts, "management_members", "The management team includes {value}.")
        add(relationship_parts, "generational_transition", "The generational-transition context is {value}.")
        add(relationship_parts, "historical_facilities", "Historical facilities include {value}.")
        add(relationship_parts, "employment_contract_type", "The employment-contract context is {value}.")
        add(relationship_parts, "economic_family_context", "The economic-family context is {value}.")

        if included("shareholder_details"):
            shareholders = profile["shareholder_details"]
            if isinstance(shareholders, list):
                relationship_parts.append(
                    "The shareholding structure is " + "; ".join(str(item) for item in shareholders) + "."
                )
        if included("credit_facility_details"):
            facilities = profile["credit_facility_details"]
            if isinstance(facilities, list):
                relationship_parts.append(
                    "Available credit facilities comprise " + "; ".join(str(item) for item in facilities) + "."
                )
        relationship = section("Relationship & Counterparty Context", " ".join(relationship_parts))

        event_parts: list[str] = []
        add(event_parts, "previous_restructuring", "The previous-restructuring status is {value}.")
        add(event_parts, "forborne", "Forborne exposure is reported: {value}.")
        add(event_parts, "forborne_non_performing_exit", "The exit from forborne non-performing status is {value}.")
        add(event_parts, "cure_period_days", "The cure period is {value} days.")
        add(event_parts, "monitoring_period_days", "The monitoring period is {value} days.")
        add(event_parts, "probation_period_days", "The probation period is {value} days.")
        add(event_parts, "protests", "Protests are recorded: {value}.")
        add(event_parts, "bankruptcies", "Bankruptcies are recorded: {value}.")
        add(event_parts, "litigation", "Litigation is reported: {value}.")
        add(event_parts, "significant_historical_events", "Significant historical events include {value}.")
        if included("relevant_event_details"):
            events = profile["relevant_event_details"]
            if isinstance(events, list):
                event_parts.append(
                    "Recorded events include " + "; ".join(str(item) for item in events) + "."
                )
        events = section("Relevant Events", " ".join(event_parts))

        return "\n\n".join((general, risk, relationship, events))
