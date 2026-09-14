# System Validation

## Purpose

Validation protects three properties:

1. deterministic credit decisioning;
2. complete and traceable evidence;
3. bounded and resilient reporting.

> **LLM output is never the source of truth for the credit assessment.**

## Validation levels

| Level | Scope |
|---|---|
| Unit | Rules, models, validators, services and policies |
| Integration | Cross-layer evidence and case aggregation |
| Workflow | Assessment → analysis → reporting propagation |
| Reporting | Prompt contract, grounding and fallback |
| Scenario | End-to-end representative domain/rule coverage |
| UI | Read-only presentation boundary |
| CI | Repository lint, type checking and test gates |

## Rule and configuration validation

The active rule inventory is defined by the valid configuration files under `config/` together with the registered implementations discovered under `src/rules/`.

Validation must protect the following invariant:

```text
Configured rule identifier
            ↓
exactly one resolvable deterministic implementation
            ↓
RuleResult
```

Tests cover configuration loading, required fields, duplicate identifiers, supported calculations/operators, severity configuration, registration/discovery and non-evaluable inputs.

The documentation deliberately does not duplicate the complete rule inventory. This avoids making the validation contract stale when the catalogue evolves.

## Determinism

For a fixed input and fixed configuration, rule evaluation must be reproducible:

```text
Same Input + Same Configuration
              ↓
        Same RuleResult
```

The deterministic path must not depend on LLM availability, provider responses or Streamlit state.

## Status validation

Section and case status are derived by deterministic services. Their policy is externalised where configured and must be tested from the actual policy contract rather than reproduced as independent constants in the UI or reporting layer.

The tests should cover:

- no triggered rule with evaluable evidence;
- one or more triggered rules;
- multiple triggered rules;
- all rules not evaluable;
- partial section evaluation;
- empty result collections where supported;
- final aggregation with critical, attention, normal and non-evaluable sections;
- configured core/contextual section behaviour;
- minimum evidence requirements for a normal final assessment.

The exact thresholds and section membership belong to the configuration under `config/final_assessment.yaml`.

## Workflow invariant

```text
Input
 ↓
Structural validation
 ↓
Domain assessments
 ↓
CreditAssessmentCase
 ↓
Final assessment
 ↓
Deterministic analysis
 ↓
Reporting
```

Reporting consumes deterministic results; it does not recreate or modify them.

## Reporting validation

Tests verify that:

- evidence from all configured domains reaches `AssessmentAnalysis`;
- `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE` remain distinguishable;
- high-severity triggered evidence is represented correctly in the reporting view;
- the prompt receives the evidence required by its structured contract;
- material indicators remain grounded;
- unsupported or altered evidence is rejected where grounding applies;
- provider or grounding failure activates deterministic fallback;
- fallback failure is propagated rather than silently hidden.

Reporting tests should refer to representative configured rules rather than hard-coding the complete production inventory.

## Scenario coverage

Demonstration scenarios use synthetic/anonymized data. Scenario tests should exercise representative combinations of domains and rule outcomes and should evolve when the input contract or assessment policy changes.

Scenario coverage complements, but does not replace, focused rule tests.

## UI boundary

The Results layer renders workflow evidence and does not recalculate:

- rule thresholds;
- rule severity;
- rule status;
- section status;
- final assessment status.

Any UI test that asserts a business decision should preferably derive the expected value from the deterministic contract or a dedicated test fixture rather than copying policy constants into presentation tests.

## Execution metadata

Execution metadata is provenance only. Tests verify execution identity, timestamp semantics, reporting mode, generator/fallback state, error classification and timing consistency.

Metadata does not participate in decisioning.

## CI gates

The repository workflow is the authoritative definition of CI. Local commands in `README.md` are convenience equivalents and should be kept aligned with the workflow.

A typical pipeline is:

```text
Install dependencies
        ↓
Lint
        ↓
Type checking
        ↓
Test suite + coverage
```

Do not treat a hard-coded coverage percentage in documentation as the source of truth; the CI configuration is authoritative.

## Validation philosophy

```text
Valid input
   ↓
Deterministic rules
   ↓
Deterministic final assessment
   ↓
Controlled analysis
   ↓
Bounded reporting
   ↓
Read-only presentation
```

LLM failure must never invalidate a deterministic assessment.

## Change impact

When the rule catalogue changes, the minimum validation impact should be assessed across:

```text
Configuration
Implementation
Discovery / registry
Rule tests
Section aggregation
Case aggregation
Analysis evidence
Reporting / grounding
Demo scenarios
UI presentation
Documentation
```

A rule addition should not require modifications to unrelated reporting or presentation logic merely because its identifier is new.
