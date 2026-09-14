# ADR-016 — Complete Rule Evidence in Reporting

**Status:** Accepted

## Context

The assessment is composed of deterministic domain sections, each of which evaluates its configured rules. Reporting based only on triggered findings would lose the distinction between risk detected, risk not detected and evidence unavailable.

For an analyst-oriented report, the reporting layer therefore needs the complete deterministic evidence set while keeping `risk_factors` focused on high-severity triggered evidence.

The ADR deliberately does not enumerate individual rule identifiers. The active catalogue is configuration-driven and may evolve independently of the reporting architecture.

## Decision

`CaseAnalysisAgent` aggregates rule evidence from every assessment section and exposes it through `AssessmentAnalysis`.

```text
Domain assessments
        ↓
Rule / section evidence
        ↓
Complete deterministic evidence
        ↓
AssessmentAnalysis
        ↓
Reporting Agent
```

Each rule preserves its deterministic outcome, including:

- `TRIGGERED`
- `NOT_TRIGGERED`
- `NOT_EVALUABLE`

The complete deterministic evidence is available to reporting. `risk_factors` remains a narrower subset containing high-severity triggered evidence.

## Consequences

### Positive

- Reporting has visibility across all configured assessment domains.
- Normal and unavailable evidence remain distinguishable from risk.
- New rules and rule families do not require rule-specific logic in the Reporting Agent.
- The deterministic assessment remains the single source of truth.
- The reporting contract remains stable as the catalogue evolves.

### Constraints

- Tests must verify complete evidence propagation.
- Reporting must not recalculate or reinterpret rule outcomes.
- UI code must consume structured workflow results rather than reproduce rule logic.
- Any new evidence type that changes the structured reporting contract must be reflected in the domain model and corresponding tests.

## Rejected alternative

Passing only triggered findings was rejected because it removes information about evaluated-but-normal rules and unavailable evidence.

## Invariant

> **Reporting may synthesize deterministic evidence, but it may not create, modify or override that evidence or the resulting credit decision.**
