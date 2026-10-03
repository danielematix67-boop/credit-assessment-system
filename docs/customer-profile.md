# Customer Profile: Implementation Reference

This document describes the Customer Profile contract currently implemented in `src/models/customer_profile_data.py`, its assessment and materiality services, and its use by the application/reporting workflow.

## Purpose and boundaries

Customer Profile is a contextual information layer alongside deterministic rule evidence. It is not a second rule engine.

- `CustomerProfileData` is the input contract.
- The Customer Profile assessment service evaluates the configured CP rules and constructs the structured profile context.
- `CustomerProfileMaterialityPolicy` selects contextual fields for the Executive Narrative.
- The detailed profile can retain the full available context; the Executive Narrative receives the material subset.
- Rule findings remain deterministic and retain their own statuses. Context fields do not become findings merely because they are informative.

## Input contract

All fields are optional unless represented by a collection with an empty-list default. Missing scalar values use `None`; list fields default to an empty list.

| Group | Fields in `CustomerProfileData` |
|---|---|
| General information | `company_name`, `counterparty_type`, `legal_form`, `sector`, `size_class`, `geography`, `business_history_years`, `operations` |
| Risk-grade evolution | `forborne_non_performing_exit`, `past_due_count`, `cure_period_days`, `monitoring_period_days`, `probation_period_days`, `minimum_regulatory_risk_grade`, `previous_risk_grade`, `risk_grade_change` |
| Statistical predictiveness | `ews_score_class`, `ews_score_notching`, `ews_score_variation`, `active_ewis`, `rating`, `rating_increments`, `rating_influential_factors`, `rating_elementary_modules`, `pd` |
| Risk group | `risk_group_interdependence`, `risk_group_independence` |
| Ownership, management and counterparty context | `shareholders`, `shareholder_roles`, `management_members`, `generational_transition`, `employment_contract_type`, `economic_family_context` |
| Banking relationship and credit history | `relationship_years`, `historical_facilities`, `previous_restructuring`, `forborne` |
| Relevant events | `protests`, `bankruptcies`, `litigation`, `significant_historical_events` |

The model is intentionally descriptive. Presence in the input model does not imply that a field is currently collected through a dedicated UI control or used in a rule. The demo scenarios and the active application input path determine which values are supplied in a given run.

## Deterministic rules versus contextual fields

The Customer Profile rule family currently uses identifiers CP001–CP005. These rules are evaluated through the normal deterministic rule path and their results can contribute to the Customer Profile section assessment.

The materiality policy treats the following profile attributes as already represented by rule evidence and excludes them from the separate contextual subset:

- `ews_score_class`
- `previous_restructuring`
- `forborne`
- `business_history_years`
- `relationship_years`

This avoids duplicating the same facts in the Executive Narrative. The rule findings remain available as rule evidence.

## Executive materiality selection

Materiality is selected before report generation by `CustomerProfileMaterialityPolicy.material_fields()`. It is deterministic and does not depend on an LLM.

### Always-material fields

When populated, these fields are selected:

- EWS notching and variation, active EWIs;
- rating, rating increments, influential factors and elementary modules, PD;
- minimum regulatory risk grade, previous risk grade and risk-grade change;
- risk-group interdependence and independence;
- forborne non-performing exit;
- protests, bankruptcies, litigation and significant historical events.

A boolean value of `False` is not selected as material.

### Conditionally material fields

The following fields are selected only when they indicate a positive/non-zero condition:

- `past_due_count`
- `cure_period_days`
- `monitoring_period_days`
- `probation_period_days`
- `generational_transition`

For numeric fields, the condition is a value greater than zero; for the boolean field, it is `True`.

Other descriptive fields are available in the full profile but are not automatically included in the Executive Summary material subset by this policy.

## Risk-grade evolution

The input contract distinguishes the prior grade from the direction/change descriptor:

- `previous_risk_grade`: the previously assigned risk grade;
- `risk_grade_change`: a descriptor of the change in the risk profile.

These are contextual fields, not independent rule outcomes. They are included in material executive context when supplied. Their interpretation in narrative must remain grounded in the supplied values; the reporting layer must not infer a numeric migration or regulatory consequence that is not present in the evidence.

## Reporting and UI implications

The reporting contract distinguishes:

| Surface | Information |
|---|---|
| Deterministic rule evidence | Results of CP rules, including status, severity and evidence |
| Detailed Customer Profile | Structured profile context available for the run |
| Executive Narrative | CP rule evidence combined with the policy-selected material context in one Customer Profile section |

The Streamlit Results UI presents workflow output. It must not independently decide materiality or recompute CP rule outcomes. If a field is added, changed or removed, review the model, service propagation, materiality policy, analysis/reporting contract, demo input and tests together.

## Maintenance checklist

When changing Customer Profile:

- [ ] Update `CustomerProfileData` and its tests.
- [ ] Verify propagation through the Customer Profile assessment service.
- [ ] Decide explicitly whether the field is rule-backed, always material, conditionally material, or full-profile-only.
- [ ] Update `CustomerProfileMaterialityPolicy` and policy tests if executive selection changes.
- [ ] Update analysis/reporting tests and narrative grounding where applicable.
- [ ] Update synthetic demo scenarios and UI input handling if the field is exposed there.
- [ ] Keep contextual facts separate from deterministic `RuleResult` evidence.
