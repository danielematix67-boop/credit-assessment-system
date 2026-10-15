# Customer Profile: Implementation Reference

This document describes the Customer Profile contract currently implemented in `src/models/customer_profile_data.py`, its deterministic assessment service, its materiality policy and its use by the application/reporting workflow.

## Purpose and boundaries

Customer Profile is a contextual information layer alongside deterministic rule evidence. It is **not a second rule engine**.

- `CustomerProfileData` is the input contract.
- `CustomerProfileAssessmentService` loads `config/customer_profile_rules.yaml`, evaluates the configured CP rules and constructs the Customer Profile section and context.
- `CustomerProfileMaterialityPolicy` deterministically computes a separate subset of contextual fields; the final Executive Narrative uses the full profile.
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

| Ownership, management and counterparty context | `shareholders`, `shareholder_roles`, `management_members`, `generational_transition`, `employment_contract_type`, `economic_family_context` |
| Banking relationship and credit history | `relationship_years`, `historical_facilities`, `previous_restructuring`, `forborne` |
| Relevant events | `protests`, `bankruptcies`, `litigation`, `significant_historical_events` |

The model is intentionally descriptive. Presence in the input model does not imply that a field is currently exposed as a dedicated UI control or used by a rule. The active application input path and synthetic demo scenario determine which values are supplied in a run.

## Deterministic Customer Profile rules

The active Customer Profile catalogue is defined by `config/customer_profile_rules.yaml` and the deterministic implementations discovered under `src/rules/`. This document intentionally does not enumerate current rule IDs, implementation class names or thresholds: those change as the catalogue evolves and are available in the configuration and source code.

Each configured rule follows the shared rule contract:

- it declares the required input field(s), trigger condition and severity policy;
- its implementation evaluates the condition deterministically;
- it returns `TRIGGERED`, `NOT_TRIGGERED` or `NOT_EVALUABLE`;
- its result is included in the Customer Profile section evidence;
- missing or invalid required evidence is not treated as a normal result.

Use the configuration as the source of truth for declarative thresholds and severity bands. Use the corresponding rule implementation and tests for specialised validation or calculations. When changing the catalogue, verify that each configured identifier resolves to exactly one discovered implementation and that the materiality policy remains aligned with any profile fields represented by rule evidence.

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
| `material_customer_profile` | Policy-selected contextual subset | Separate contextual use; not the fixed narrative block |

The analysis layer computes the separate material subset before reporting. The final Executive Narrative's fixed Customer Profile block is sourced from the full profile instead.

### Detailed narrative formatting contract

The deterministic detailed profile uses these four headings in this canonical order:

1. **General Information**
2. **Risk Profile & Predictiveness**
3. **Relationship & Counterparty Context**
4. **Relevant Events**

Each heading is a distinct block and must remain present even when its data are sparse. The analysis parser maps blocks by their explicit heading, not by assuming that every block contains populated fields. Empty blocks use `No additional information available.` rather than disappearing and shifting the meaning of subsequent sections.

When company identity or business context is available, **General Information** begins with a short natural introduction describing the customer and relevant high-level business details. The analysis agent now assembles the available profile attributes into fluent prose instead of a repeated `Label is value` or bullet-style inventory. List-valued fields are rendered as readable text, and Boolean values use human-readable wording. Related records remain associated with their intended thematic section: shareholders, ownership and credit facilities belong to **Relationship & Counterparty Context**; protests, bankruptcies, litigation and significant historical events belong to **Relevant Events**. Missing scalar fields are omitted instead of being printed as empty values or raw `field=value` pairs. This is a presentation change only: it does not alter materiality, rule evidence or assessment status.

The detailed analysis retains the four canonical section identities so each block can be mapped reliably even when some fields are empty. This should not be confused with Executive Narrative formatting: the reporting layer combines the full deterministic profile context into compact prose and removes nested profile headings to avoid duplicating the hierarchy inside the Customer Profile narrative area.

The reporting boundary is:

```text
Full profile context
        ↓
AssessmentAnalysis.customer_profile
        ↓
ReportingAgent post-processing
        ↓
Fixed Customer Profile block
        ↓
Triggered Customer Profile rule findings
```

The full profile block is rendered deterministically and replaces any LLM-generated Customer Profile prose after the selected generator returns. This makes the context identical in deterministic, Gemini, Ollama and fallback modes. Risk-group interdependence/independence descriptions are excluded from narrative output. `material_customer_profile` remains a separate policy-selected model field but does not define the fixed narrative block.

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
| Executive Narrative | Full deterministic profile context followed by triggered CP rule findings in one Customer Profile section |

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
