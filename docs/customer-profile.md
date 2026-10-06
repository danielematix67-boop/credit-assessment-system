# Customer Profile: Implementation Reference

This document describes the Customer Profile contract currently implemented in `src/models/customer_profile_data.py`, its deterministic assessment service, its materiality policy and its use by the application/reporting workflow.

## Purpose and boundaries

Customer Profile is a contextual information layer alongside deterministic rule evidence. It is **not a second rule engine**.

- `CustomerProfileData` is the input contract.
- `CustomerProfileAssessmentService` loads `config/customer_profile_rules.yaml`, evaluates the configured CP rules and constructs the Customer Profile section and context.
- `CustomerProfileMaterialityPolicy` deterministically selects contextual fields for Executive Narrative reporting.
- `CustomerProfileAnalysis` organises the profile into four reporting sections.
- `AssessmentAnalysis` keeps both the full `customer_profile` and the bounded `material_customer_profile` representation.
- Rule findings remain deterministic and retain their own statuses. Context fields do not become findings merely because they are informative.

The boundary is therefore:

```text
CustomerProfileData
        ↓
CustomerProfileAssessmentService
        ├── RuleResult evidence
        └── profile context
                    ↓
             CaseAnalysisAgent
                ↙        ↘
       full profile    material context
                            ↓
              CustomerProfileMaterialityPolicy
                            ↓
                    Executive Narrative
```

## Input contract

All scalar fields are optional unless a run supplies them. Collection fields default to empty lists.

| Group | Fields in `CustomerProfileData` |
|---|---|
| General information | `company_name`, `counterparty_type`, `legal_form`, `sector`, `size_class`, `geography`, `business_history_years`, `operations` |
| Risk-grade evolution | `forborne_non_performing_exit`, `past_due_count`, `cure_period_days`, `monitoring_period_days`, `probation_period_days`, `minimum_regulatory_risk_grade`, `previous_risk_grade`, `risk_grade_change` |
| Statistical predictiveness | `ews_score_class`, `ews_score_notching`, `ews_score_variation`, `active_ewis`, `rating`, `rating_notching`, `rating_influential_factors`, `rating_elementary_modules`, `pd` |
| Risk group | `risk_group_interdependence`, `risk_group_independence` |
| Ownership, management and counterparty context | `shareholders`, `shareholder_roles`, `management_members`, `generational_transition`, `employment_contract_type`, `economic_family_context` |
| Banking relationship and credit history | `relationship_years`, `historical_facilities`, `previous_restructuring`, `forborne` |
| Relevant events | `protests`, `bankruptcies`, `litigation`, `significant_historical_events` |

The model is intentionally descriptive. Presence in the input model does not imply that a field is currently exposed as a dedicated UI control or used by a rule. The active application input path and synthetic demo scenario determine which values are supplied in a run.

## Deterministic Customer Profile rules

The active Customer Profile catalogue currently contains CP001–CP005. These identifiers are loaded from `config/customer_profile_rules.yaml` and resolved through the normal rule discovery/registry mechanism.

| Rule | Current implementation | Input | Deterministic meaning |
|---|---|---|---|
| CP001 | `EwsScoreClassRule` | `ews_score_class` | Triggers for a non-GREEN EWS class; YELLOW/ORANGE are MEDIUM and LIGHT_RED is HIGH |
| CP002 | `PreviousRestructuringRule` | `previous_restructuring` | Triggers when a previous restructuring is present |
| CP003 | `BusinessHistoryRule` | `business_history_years` | Triggers when business history is at or below the configured threshold; severity is configuration-driven |
| CP004 | `ForborneExposureRule` | `forborne` | Triggers when the forborne flag is `True`; MEDIUM severity when triggered |
| CP005 | `ShortBankingRelationshipRule` | `relationship_years` | Triggers when the banking relationship is at or below the configured threshold |

The rule implementations preserve the standard three-way outcome:

```text
TRIGGERED
NOT_TRIGGERED
NOT_EVALUABLE
```

In particular:

- CP001 explicitly validates the EWS enum/value;
- CP004 explicitly validates that the forborne input is boolean;
- the other current CP rules use the shared configured-value comparison path;
- missing or invalid required evidence produces `NOT_EVALUABLE` rather than an assumed normal result.

The exact thresholds and declarative parameters remain in `config/customer_profile_rules.yaml`, rather than being duplicated in this document.

## Customer Profile section behaviour

`CustomerProfileAssessmentService` evaluates all configured CP rules and retains their complete results in the section evidence.

Only triggered results become `RuleFinding` objects and receive deterministic comments for the findings presentation. The complete evidence list still contains non-triggered and non-evaluable results so that reporting can distinguish:

- a condition that was evaluated and did not trigger;
- a condition that triggered;
- a condition that could not be evaluated.

If no profile data are supplied, the Customer Profile section is `NOT_EVALUABLE`. If profile data exist but none of the configured rules can be evaluated, the service records that limitation rather than interpreting the situation as evidence of normality.

The service also propagates the structured profile context into the assessment case. This context is what later feeds detailed profile presentation and deterministic materiality selection.

## Deterministic rules versus contextual fields

The materiality policy treats the following attributes as already represented by rule evidence and therefore excludes them from the separate contextual subset:

- `ews_score_class`;
- `previous_restructuring`;
- `forborne`;
- `business_history_years`;
- `relationship_years`.

This prevents the same fact from appearing once as a deterministic rule finding and again as contextual profile text.

This does **not** mean that these fields disappear from the full Customer Profile. They remain part of the structured profile context and can be represented through the deterministic rule evidence and detailed profile views.

## Executive materiality selection

Materiality is selected before report generation by `CustomerProfileMaterialityPolicy.material_fields()`. It is deterministic and does not depend on an LLM.

### Always-material fields

When populated, the policy selects:

- EWS notching and variation;
- active EWIs;
- rating, rating increments, influential factors and elementary modules;
- PD;
- minimum regulatory risk grade, previous risk grade and risk-grade change;
- risk-group interdependence and independence;
- forborne non-performing exit;
- protests, bankruptcies, litigation and significant historical events.

A boolean value of `False` is not selected.

### Conditionally material fields

The policy selects the following only when they indicate a positive/non-zero condition:

- `past_due_count`;
- `cure_period_days`;
- `monitoring_period_days`;
- `probation_period_days`;
- `generational_transition`.

For numeric fields, the condition is a value greater than zero. For `generational_transition`, the condition is `True`.

Other descriptive fields remain available in the full profile but are not automatically selected for the Executive Summary by the current materiality policy.

## Customer Profile reporting model

`CustomerProfileAnalysis` presents the profile through four ordered sections:

1. **General Information**
2. **Risk Profile & Predictiveness**
3. **Relationship & Counterparty Context**
4. **Relevant Events**

`AssessmentAnalysis` exposes two profile views:

| Field | Scope | Purpose |
|---|---|---|
| `customer_profile` | Full available structured profile | Detailed Customer Profile presentation |
| `material_customer_profile` | Policy-selected contextual subset | Executive Narrative |

The analysis layer therefore performs the materiality decision before the reporting layer is invoked.

The reporting boundary is:

```text
Full profile context
        ↓
CustomerProfileMaterialityPolicy
        ↓
material_customer_profile
        ↓
ReportPromptBuilder / DeterministicReportGenerator
        ↓
One consolidated Customer Profile section
```

Both the LLM-backed and deterministic reporting paths receive the same bounded material contextual profile. Neither path decides independently which profile fields are material.

## Risk-grade evolution

The regulatory-grade context uses categorical credit-status values rather than numeric scores:

- `minimum_regulatory_risk_grade`: minimum/current regulatory grade represented by the case, using the controlled vocabulary **Bonis, Past Due, Unlikely to Pay, Bad Loan**;
- `previous_risk_grade`: previous regulatory grade, using the same vocabulary;
- `risk_grade_change`: the observed transition between regulatory grades, expressed as a categorical transition such as `Bonis to Past Due`.

These are contextual fields, not independent rule outcomes. Reporting must preserve the supplied categories and must not convert them into numeric scores or infer a migration that is not present in the input.

EWS notching and rating notching are also categorical/contextual fields. They are optional and are represented as descriptive text when present; they are **not numeric notch counts**.

## Reporting and UI implications

The reporting contract distinguishes:

| Surface | Information |
|---|---|
| Deterministic rule evidence | Complete CP rule results, including status, severity and evidence |
| Detailed Customer Profile | Structured profile context available for the run |
| Executive Narrative | CP rule evidence combined with policy-selected material context in one Customer Profile section |

The Streamlit Results UI presents workflow output. It does not independently decide materiality or recompute CP rule outcomes.

## Maintenance checklist

When changing Customer Profile:

- [ ] Update `CustomerProfileData` and its tests.
- [ ] Verify propagation through `CustomerProfileAssessmentService`.
- [ ] If a rule changes, update the YAML catalogue and corresponding implementation/tests.
- [ ] Decide explicitly whether a new field is rule-backed, always material, conditionally material, or full-profile-only.
- [ ] Update `CustomerProfileMaterialityPolicy` and its tests if Executive Summary selection changes.
- [ ] Verify `AssessmentAnalysis.customer_profile` and `material_customer_profile` remain correctly populated.
- [ ] Update analysis/reporting tests and grounding tests where applicable.
- [ ] Update synthetic demo scenarios and UI input handling if the field is exposed there.
- [ ] Keep contextual facts separate from deterministic `RuleResult` evidence.
- [ ] Update documentation only where the implementation contract or user-visible behaviour actually changes.
