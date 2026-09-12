# ADR-016 — Complete Rule Evidence in the Reporting Layer

**Status:** Accepted

## Context

The credit-assessment case contains multiple deterministic macro-areas. A reporting layer that receives only triggered findings cannot distinguish detected risk from evaluated-but-normal evidence or unavailable evidence.

This is particularly important for an analyst-oriented report: the narrative should be grounded in the complete deterministic assessment, while risk drivers remain a focused subset.

## Decision

`CaseAnalysisAgent` aggregates deterministic rule evidence from every assessment section and exposes it through `AssessmentAnalysis`.

The reporting input therefore includes:

```text
Customer Profile      → CP001–CP002
Financial Analysis    → R001–R007
Behavioural Analysis  → B001–B004
Debt Sustainability   → DS001–DS003
                         ↓
                 Complete Rule Evidence
                         ↓
                 AssessmentAnalysis
                         ↓
                  Reporting Agent
```

For each rule, the analysis layer preserves the outcome:

- `TRIGGERED`;
- `NOT_TRIGGERED`;
- `NOT_EVALUABLE`.

`key_findings` is the reporting collection and contains the complete rule evidence. `rule_evidence` explicitly exposes the same complete deterministic evidence for consumers that need a dedicated field.

`risk_factors` remains a narrower collection containing only high-severity triggered evidence.

## Consequences

### Positive

- Reporting has visibility over every configured assessment domain.
- The narrative can distinguish risk signals from evaluated normal outcomes.
- Missing evidence remains explicitly represented as `NOT_EVALUABLE`.
- Adding a new rule family does not require rule-specific logic inside the Reporting Agent.
- The deterministic Rule Engine remains the sole source of truth.

### Constraints

- Tests must verify that complete evidence is propagated from all sections.
- Reporting must not reinterpret or recalculate rule outcomes.
- Presentation code must continue consuming structured workflow outputs rather than reproducing rule logic.

## Rejected Alternative

Passing only triggered findings to the reporting layer was rejected because it loses information about non-triggered and non-evaluable rules and makes the narrative input incomplete.

## Invariant

> **The reporting layer may synthesize complete deterministic evidence, but it may not create, modify or override the evidence or the resulting credit decision.**
