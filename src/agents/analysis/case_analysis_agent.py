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
        """Map the deterministic profile narrative into stable reporting sections."""
        sections = [part.strip() for part in summary.split("\n\n")]
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
        """Build a discursive contextual customer-profile narrative for reporting."""
        def present(value: object, key: str | None = None) -> bool:
            return (
                value not in (None, "", [], {})
                and (fields is None or key is None or key in fields)
            )

        def as_text(value: object) -> str:
            if isinstance(value, list):
                return ", ".join(str(item) for item in value)
            if isinstance(value, bool):
                return "Yes" if value else "No"
            return str(value)

        def get(key: str) -> object:
            return profile.get(key)

        company = get("company_name")
        identity_parts: list[str] = []
        if present(get("size_class"), "size_class"):
            identity_parts.append(f"a {as_text(get('size_class')).lower()} company")
        if present(get("sector"), "sector"):
            identity_parts.append(
                f"operating in the {as_text(get('sector')).lower()} sector"
            )
        if present(get("geography"), "geography"):
            identity_parts.append(f"based in {as_text(get('geography'))}")

        if identity_parts:
            subject = as_text(company) if present(company) else "The customer"
            identity = f"{subject} is {', '.join(identity_parts)}."
        elif present(company):
            identity = f"{as_text(company)} is the customer under assessment."
        else:
            identity = ""

        if present(get("operations"), "operations"):
            identity += f" Its activities include {as_text(get('operations'))}."
        if present(get("business_history_years"), "business_history_years"):
            years = get("business_history_years")
            unit = "year" if years == 1 else "years"
            identity += f" The business has an operating history of {years} {unit}."

        risk_parts: list[str] = []
        if present(get("minimum_regulatory_risk_grade"), "minimum_regulatory_risk_grade"):
            risk_parts.append(
                f"the minimum regulatory risk grade is {as_text(get('minimum_regulatory_risk_grade'))}"
            )
        if present(get("previous_risk_grade"), "previous_risk_grade"):
            risk_parts.append(
                f"the previous risk grade was {as_text(get('previous_risk_grade'))}"
            )
        if present(get("risk_grade_change"), "risk_grade_change"):
            risk_parts.append(
                f"the risk-grade change is {as_text(get('risk_grade_change'))}"
            )
        if present(get("past_due_count"), "past_due_count"):
            count = get("past_due_count")
            risk_parts.append(f"{count} past-due positions are reported")
        if present(get("ews_score_class"), "ews_score_class"):
            risk_parts.append(
                f"the EWS Score class is {as_text(get('ews_score_class'))}"
            )
        if present(get("ews_score_notching"), "ews_score_notching"):
            risk_parts.append(
                f"EWS notching is {as_text(get('ews_score_notching'))}"
            )
        if present(get("ews_score_variation"), "ews_score_variation"):
            risk_parts.append(
                f"EWS variation is {as_text(get('ews_score_variation'))}"
            )
        if present(get("active_ewis"), "active_ewis"):
            risk_parts.append(
                f"active EWIs include {as_text(get('active_ewis'))}"
            )
        if present(get("rating"), "rating"):
            risk_parts.append(f"the rating is {as_text(get('rating'))}")
        if present(get("rating_increments"), "rating_increments"):
            risk_parts.append(
                f"rating increments include {as_text(get('rating_increments'))}"
            )
        if present(get("rating_influential_factors"), "rating_influential_factors"):
            risk_parts.append(
                f"the main influential rating factors include {as_text(get('rating_influential_factors'))}"
            )
        if present(get("rating_elementary_modules"), "rating_elementary_modules"):
            risk_parts.append(
                f"the elementary rating modules include {as_text(get('rating_elementary_modules'))}"
            )
        if present(get("pd"), "pd"):
            risk_parts.append(f"the reported PD is {as_text(get('pd'))}")

        risk = ""
        if risk_parts:
            risk = "The available risk-profile information indicates that " + ", ".join(risk_parts) + "."

        relationship_parts: list[str] = []
        if present(get("relationship_years"), "relationship_years"):
            years = get("relationship_years")
            unit = "year" if years == 1 else "years"
            relationship_parts.append(f"a banking relationship of {years} {unit}")
        if present(get("historical_facilities"), "historical_facilities"):
            relationship_parts.append(
                f"historical facilities including {as_text(get('historical_facilities'))}"
            )
        if present(get("risk_group_interdependence"), "risk_group_interdependence"):
            relationship_parts.append(
                f"{as_text(get('risk_group_interdependence'))} interdependence with the risk group"
            )
        if present(get("risk_group_independence"), "risk_group_independence"):
            relationship_parts.append(
                f"{as_text(get('risk_group_independence')).lower()} independence within the risk group"
            )
        if present(get("shareholders"), "shareholders"):
            relationship_parts.append(
                f"shareholders including {as_text(get('shareholders'))}"
            )
        if present(get("shareholder_roles"), "shareholder_roles"):
            relationship_parts.append(
                f"shareholder roles including {as_text(get('shareholder_roles'))}"
            )
        if present(get("management_members"), "management_members"):
            relationship_parts.append(
                f"management comprising {as_text(get('management_members'))}"
            )
        generational_transition = get("generational_transition")
        if present(generational_transition, "generational_transition"):
            if generational_transition is True:
                relationship_parts.append("a generational transition")
            elif generational_transition is False:
                relationship_parts.append("no reported generational transition")
        if present(get("employment_contract_type"), "employment_contract_type"):
            relationship_parts.append(
                f"an employment contract described as {as_text(get('employment_contract_type'))}"
            )
        if present(get("economic_family_context"), "economic_family_context"):
            relationship_parts.append(
                f"an economic-family context described as {as_text(get('economic_family_context'))}"
            )

        relationship = ""
        if relationship_parts:
            relationship = (
                "The broader relationship and counterparty context includes "
                + ", ".join(relationship_parts)
                + "."
            )

        event_parts: list[str] = []
        if present(get("previous_restructuring"), "previous_restructuring") and get("previous_restructuring") is True:
            event_parts.append("a previous restructuring")
        if present(get("forborne"), "forborne") and get("forborne") is True:
            event_parts.append("a forborne exposure")
        forborne_exit = get("forborne_non_performing_exit")
        if present(forborne_exit, "forborne_non_performing_exit"):
            if forborne_exit is True:
                event_parts.append("an exit from a forborne non-performing exposure")
            elif forborne_exit is False:
                event_parts.append(
                    "no reported exit from a forborne non-performing exposure"
                )
        if present(get("cure_period_days"), "cure_period_days"):
            event_parts.append(f"a cure period of {as_text(get('cure_period_days'))} days")
        if present(get("monitoring_period_days"), "monitoring_period_days"):
            event_parts.append(f"a monitoring period of {as_text(get('monitoring_period_days'))} days")
        if present(get("probation_period_days"), "probation_period_days"):
            event_parts.append(f"a probation period of {as_text(get('probation_period_days'))} days")
        for label, key in (
            ("protests", "protests"),
            ("bankruptcies", "bankruptcies"),
            ("litigation", "litigation"),
            ("significant historical events", "significant_historical_events"),
        ):
            if present(get(key), key):
                event_parts.append(f"{label}: {as_text(get(key))}")

        events = ""
        if event_parts:
            events = "Relevant events and credit-history information include " + ", ".join(event_parts) + "."

        return "\n\n".join((identity, risk, relationship, events))
