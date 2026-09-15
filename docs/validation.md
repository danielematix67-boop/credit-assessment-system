# System Validation

## What validation means

**In simple terms:** validation is the set of checks that makes sure the system is using acceptable data, applying the intended rules consistently, and producing a report that remains faithful to the assessment.

**Technical meaning:** validation protects three core properties:

1. deterministic credit assessment;
2. complete and traceable evidence;
3. bounded and resilient reporting.

> **The LLM is never the source of truth for the credit assessment.**

## What is being validated?

The project validates different layers because a system can be correct at one level and still fail when components interact.

| Level | In simple terms | Technical scope |
|---|---|---|
| Unit | Does one component work correctly? | Rules, models, validators, services and policies |
| Integration | Do components work correctly together? | Cross-layer evidence and case aggregation |
| Workflow | Does information survive the whole process? | Assessment → analysis → reporting |
| Reporting | Is the generated report faithful to the evidence? | Prompt contract, grounding and fallback |
| Scenario | Does a realistic case behave correctly? | Representative combinations of domains and rule outcomes |
| UI | Does the interface display the result without changing it? | Presentation boundary |
| CI | Does the repository pass automated quality gates? | Linting, type checking, tests and coverage |

## Rule and configuration validation

**In simple terms:** every configured risk check must correspond to one real, deterministic implementation that the application can find and execute.

**Technical meaning:** the active rule inventory is defined by valid configuration catalogues under `config/` together with registered implementations discovered under `src/rules/`.

The expected relationship is:

```text
Configured rule identifier
            ↓
Exactly one resolvable deterministic implementation
            ↓
Rule evaluation
            ↓
RuleResult
```

Validation covers configuration loading, required fields, duplicate identifiers, supported calculations/operators, severity configuration, registration/discovery and non-evaluable inputs.

The documentation deliberately does not copy the complete rule inventory because that inventory can evolve independently of the architecture.

## Determinism

**In simple terms:** if the same valid information is analysed with the same settings, the assessment should not randomly change.

**Technical meaning:** for a fixed input and fixed configuration, rule evaluation must be reproducible.

```text
Same Input + Same Configuration
              ↓
        Same RuleResult
```

The deterministic assessment path must not depend on LLM availability, provider responses or Streamlit state.

## Rule outcomes

Three outcomes must remain distinct:

- **`TRIGGERED`** — the check was possible and its configured condition was met.
- **`NOT_TRIGGERED`** — the check was possible and its configured condition was not met.
- **`NOT_EVALUABLE`** — the check could not be performed because the required information was unavailable or unsuitable.

The third state is important. **`NOT_EVALUABLE` does not mean that the condition is absent.** It means that the system does not have enough evidence to determine the result.

## Status aggregation

**In simple terms:** individual checks are combined to produce results for larger parts of the assessment and, ultimately, for the whole credit position.

**Technical meaning:** deterministic services derive section and case status from rule results according to the configured assessment policy.

Tests should cover at least:

- no triggered rule with evaluable evidence;
- one or more triggered rules;
- multiple triggered rules;
- all rules not evaluable;
- partial section evaluation;
- supported empty result collections;
- final aggregation involving critical, attention, normal and non-evaluable sections;
- configured core/contextual section behaviour;
- minimum evidence requirements for a normal final assessment.

Exact thresholds and section membership belong to the configuration under `config/final_assessment.yaml`; they should not be independently reproduced in the UI or reporting layer.

## End-to-end workflow invariant

The expected information flow is:

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
 ↓
Presentation
```

Each stage has a different responsibility. Reporting consumes deterministic results; it does not recreate or modify them.

## Reporting validation

Reporting tests verify that:

- evidence from all configured domains reaches the analysis model;
- `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE` remain distinguishable;
- high-severity triggered evidence is represented correctly;
- the prompt receives the evidence required by its structured contract;
- material indicators remain grounded in authoritative evidence;
- unsupported or altered evidence is rejected where grounding applies;
- provider or grounding failure activates the deterministic fallback where configured;
- fallback failure is propagated rather than silently hidden.

Tests should use representative configured rules rather than maintaining a duplicate production inventory inside reporting tests.

## Scenario coverage

Demonstration scenarios use synthetic/anonymized data.

**In simple terms:** scenarios are realistic examples used to check that several parts of the system behave correctly together.

They complement focused unit and integration tests; they do not replace them.

Scenario coverage should evolve when the input contract, rule catalogue or assessment policy changes.

## Presentation boundary

The Results/UI layer displays workflow evidence. It must not recalculate:

- rule thresholds;
- rule severity;
- rule status;
- section status;
- final assessment status.

A UI test that checks a business decision should preferably obtain the expected value from the deterministic contract or a dedicated fixture rather than copying policy constants into presentation code.

## Execution metadata

Execution metadata describes **how a run happened**, not **what the credit decision is**.

It can include information such as execution identity, timestamp, reporting mode, generator/fallback state, error classification and timings.

Tests should verify metadata consistency, while keeping metadata separate from decision evidence.

## CI gates

The CI workflow is the authoritative definition of automated repository checks. Local commands are convenience equivalents.

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

Do not treat a coverage percentage written in Markdown as authoritative; the CI workflow is the source of truth.

## Validation philosophy

The overall principle is:

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

An LLM failure must never invalidate a valid deterministic assessment.

## Change impact

When a rule catalogue changes, review the complete path:

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
Presentation
Documentation
```

A rule addition should not require unrelated rule-specific branches in reporting or presentation logic merely because a new identifier has been introduced.
