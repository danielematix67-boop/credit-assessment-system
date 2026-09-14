# ADR-016 — Complete Rule Evidence in Reporting

**Status:** Accepted

## Context

The assessment covers four deterministic domains. Reporting based only on triggered findings would lose the distinction between risk detected, risk not detected and evidence unavailable.

For an analyst-oriented report, the reporting layer therefore needs the complete deterministic evidence set while keeping `risk_factors` focused on high-severity risk.

## Decision

`CaseAnalysisAgent` aggregates rule evidence from every assessment section and exposes it through `AssessmentAnalysis`.

```text
Customer Profile      → CP001–CP003
Financial Analysis    → R001–R007
Behavioural Analysis  → B001–B004
Debt Sustainability   → DS001–DS003
                         ↓
                 Complete Evidence
                         ↓
                 AssessmentAnalysis
                         ↓
                  Reporting Agent
```

Each rule preserves one of:

- `TRIGGERED`
- `NOT_TRIGGERED`
- `NOT_EVALUABLE`

The complete deterministic evidence is available to reporting. `risk_factors` remains a narrower subset containing high-severity triggered evidence.

## Consequences

### Positive

- Reporting has visibility across all four domains.
- Normal and unavailable evidence remain distinguishable from risk.
- New rule families do not require rule-specific logic in the Reporting Agent.
- The deterministic assessment remains the single source of truth.

### Constraints

- Tests must verify complete evidence propagation.
- Reporting must not recalculate or reinterpret rule outcomes.
- UI code must consume structured workflow results rather than reproduce rule logic.

## Rejected Alternative

Passing only triggered findings was rejected because it removes information about evaluated-but-normal rules and unavailable evidence.

## Invariant

> **Reporting may synthesize deterministic evidence, but it may not create, modify or override that evidence or the resulting credit decision.**
