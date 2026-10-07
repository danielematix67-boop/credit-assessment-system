# Architecture

## Overview

The system is a deterministic, multi-domain credit-assessment application with an optional AI-assisted reporting layer.

> **The deterministic assessment decides; AI explains.**

Assessment is completed before reporting starts. LLM providers are downstream reporting components and have no authority over the structured credit assessment.

Core business logic lives under `src/`. Streamlit presentation and application orchestration live under `app/`.

## System flow

```text
CreditPosition + domain inputs
              ↓
      Structural validation
              ↓
       Domain assessments
              ↓
     CreditAssessmentCase
              ↓
    FinalAssessmentService
              ↓
       Final assessment
              ↓
   Deterministic case analysis
              ↓
       Reporting Agent
          ↙          ↘
 Deterministic       Optional LLM
   generator       provider(s)
          ↘          ↙
             Report
```

The rule evaluation path is deterministic. Reporting is a separate concern.

## Domains and rule catalogue

The assessment is organised into macro-areas. Each domain owns its inputs, rule catalogue and rule evidence. The active rule inventory is **not duplicated in this document**; it is defined by the valid configuration catalogues and registered implementations at runtime.

This is intentional: adding or removing a rule should not require rewriting the architecture document.

The architecture is catalogue-independent: the number of domains, rule identifiers and rule counts may evolve without changing the architectural model described here.

## Rule architecture

```text
config/<domain>_rules.yaml
          ↓
   RuleConfigLoader
          ↓
 Rule configuration objects
          ↓
 Automatic rule discovery
          ↓
      Rule registry
          ↓
  configured rule_id
          ↓
  Concrete Rule implementation
          ↓
       RuleResult
```

Configuration contains declarative policy parameters such as input fields, calculation, trigger operator, threshold, severity, severity direction, severity bands and comment templates.

Concrete Python rule classes implement deterministic execution and specialised business semantics. The shared `Rule` base class provides reusable value resolution, trigger comparison, severity resolution and `NOT_EVALUABLE` handling.

A configured rule must resolve to a registered implementation. Central services must not contain rule-specific branches.

See [`rules.md`](rules.md) for the complete rule-development lifecycle.

## Customer Profile context and materiality

Customer Profile combines two complementary layers:

```text
CustomerProfileData
        ↓
Customer Profile Assessment
        ├── deterministic RuleResult evidence
        └── contextual profile information
                    ↓
          CaseAnalysisAgent
             ↙           ↘
      full profile    material profile
                          ↓
            CustomerProfileMaterialityPolicy
                          ↓
                 Executive Summary
```

The contextual profile is represented by `CustomerProfileAnalysis`, rather than by pseudo-rules. This model preserves four reporting areas:

- General Information;
- Risk Profile & Predictiveness;
- Relationship & Counterparty Context;
- Relevant Events.

Deterministic customer-profile rules remain part of the authoritative assessment path and can contribute to the Customer Profile section status. Descriptive fields such as business activity, ownership context, active EWIs and historical context do not automatically become `RuleResult` objects.

For Executive Summary generation, `CustomerProfileMaterialityPolicy` deterministically selects material contextual fields before reporting. Fields already represented by deterministic Customer Profile rules (currently CP001–CP005) are excluded from the material contextual subset, preventing duplicate facts. The full profile remains available for detailed profile presentation, while only the selected material context is exposed to the Executive Narrative. The reporting/LLM layer therefore does not decide what is material; it only organises or verbalises the deterministic selection.

This separation is important because **customer context is broader than rule evidence**, while executive reporting requires a bounded subset of that context. The Executive Narrative must render the Customer Profile rule evidence and material contextual profile in one consolidated Customer Profile section rather than as duplicate sections.

## Input validation boundary

`CreditPositionValidator` runs before assessment and protects structural input integrity. Business-specific constraints remain in the relevant rule/domain implementation.

```text
Input
  ↓
Structural validation
  ↓
Rule evaluation
  ↓
Section results
  ↓
Case aggregation
```

Missing evidence can remain represented as `None` so a rule can explicitly return `NOT_EVALUABLE` rather than treating absence as a normal observation.

## Deterministic comments and evidence

The `src/comments` package is intentionally separate from the LLM reporting layer. `CommentEngine` creates deterministic explanatory text for triggered rules from the same `RuleResult` objects used by the assessment pipeline.

These comments are evidence-preserving and traceable; they explain what happened, but they do not decide the credit outcome. They are part of the deterministic evidence chain, not a second adjudication layer.

## Section assessment

Rule results are aggregated into section-level status by the assessment layer. The rule itself never decides the status of another rule, another section or the final case.

The exact section-status policy is part of the deterministic assessment contract and should be validated by tests rather than duplicated as constants throughout documentation.

## Final assessment policy

`FinalAssessmentService` loads `FinalAssessmentPolicy`, which is configured in `config/final_assessment.yaml`.

The policy defines, among other things:

- how a critical section affects the case;
- how attention sections are counted for escalation;
- which sections are considered core versus contextual;
- the minimum evidence required for a normal case assessment;
- the status used when evidence is insufficient;
- limitation messages for partial evaluation.

The policy distinguishes **core** sections from **contextual** sections. Core sections participate explicitly in the current escalation logic, while contextual sections provide additional assessment context without necessarily driving the final status.

```text
Section assessments
        ↓
FinalAssessmentPolicy
        ↓
FinalAssessmentService
        ↓
FinalAssessment
```

This makes aggregation policy independently reviewable and avoids embedding thresholds in the UI or reporting layer.

## Configuration

```text
config/
├── <domain>_rules.yaml
└── final_assessment.yaml
```

The concrete filenames are implementation details. The important architectural contract is that rule parameters and final-assessment policy are externalised and loaded before deterministic execution begins.

## Reporting boundary

Reporting consumes structured deterministic evidence produced by the assessment workflow.

The reporting layer may:

- organise evidence;
- generate analyst-oriented narrative;
- preserve material indicators;
- use deterministic fallback.

It may not:

- evaluate or recalculate rules;
- modify rule results or severity;
- modify section or final status;
- turn missing evidence into positive evidence;
- introduce unsupported factual or numerical claims.

```text
Deterministic evidence
        ↓
Primary reporting generator
        ↓
Grounding validation
     ↙          ↘
 valid       invalid/failure
  ↓               ↓
Report      Deterministic fallback
```

A provider failure changes the reporting path, not the assessment.

## Results UI

The Results experience presents the workflow output through a compact hierarchy:

```text
Executive assessment
        ↓
Assessment by macro-area
        ↓
Executive narrative
```

The macro-area evidence surface is authoritative for the UI. Technical rule inspection is progressively disclosed from the same structured results.

The UI does not recalculate thresholds, severity, section status or final status.

## UI and workflow boundaries

The `app/` layer is separated into interface and orchestration responsibilities. `app/ui/` contains Streamlit presentation, input-source rendering, result views and components, while `app/workflow/` constructs and invokes the assessment workflow. The current input-source screen exposes **Excel Upload as the sole data source**: users upload a workbook, select one of its validated `scenario_id` values and review the mapped domain objects before execution. The repository's built-in `app/demo_scenarios.py` catalog is not used by the Streamlit input flow.

The Results UI renders the latest workflow result stored in Streamlit session state. It includes an executive assessment header, reporting provenance, final and macro-area statuses, a filterable rule-evidence dashboard, individual rule details and the Executive Narrative. These are presentation views over structured workflow output; they do not recalculate business rules or final status.

This boundary matters because business logic remains in `src/`; the UI layer is responsible for presentation and user interaction only. See [`application-workflow.md`](application-workflow.md) for the current application sequence and visible interface.

## Project structure

The source tree is organised by responsibility rather than by a manually maintained list of individual rules:

```text
credit-assessment-system/
├── app/                 # Streamlit presentation and orchestration
├── config/              # Declarative rule and final-assessment policy
├── src/
│   ├── agents/          # Analysis/reporting orchestration
│   ├── comments/        # Deterministic comments/evidence support
│   ├── config/          # Configuration loading and policy objects
│   ├── engine/          # Rule execution
│   ├── llm/             # Provider abstractions/integrations
│   ├── models/          # Domain and workflow models
│   ├── rules/           # Rule abstractions, discovery and implementations
│   └── services/        # Assessment and workflow services
├── docs/                # Technical documentation and ADRs
└── tests/               # Unit, integration, workflow, reporting and UI tests
```

The authoritative structure is the repository tree itself. Documentation intentionally avoids enumerating every concrete rule module.

## Demo data

Demonstration scenarios are synthetic. They exist to exercise representative assessment paths and should evolve with the input contract and catalogue.

Production or confidential banking data must not be committed to the repository.

## Execution metadata

Workflow metadata records execution provenance such as execution identity, UTC timestamp, reporting mode, generator/fallback state, error category and timings.

Metadata is observational and does not participate in credit decisioning.

## Quality boundary

The repository CI defines the authoritative quality gate. The local commands in `README.md` mirror the configured lint, type-checking and test/coverage checks.

Documentation should not hard-code coverage percentages or runtime versions unless they are part of the current supported environment and are intentionally treated as compatibility requirements.

## Architectural invariants

1. Deterministic rule evaluation owns credit evidence.
2. Rule configuration is externalised from specialised rule execution.
3. Every configured rule identifier must resolve to a registered implementation.
4. `NOT_EVALUABLE` is distinct from `NOT_TRIGGERED`.
5. Section and case aggregation remain outside individual rules.
6. Final-assessment policy is loaded separately from rule configuration.
7. Reporting consumes structured evidence and cannot alter decision facts.
8. LLM providers are optional and replaceable.
9. LLM or grounding failure cannot invalidate the deterministic assessment.
10. Streamlit does not own business logic.
11. Execution metadata is observational.
12. The Results UI consumes workflow results rather than recalculating them.
13. Customer Profile context is separated from deterministic rule evidence.
14. Executive Summary customer-profile materiality is selected deterministically before reporting.
