# System Validation

## Purpose

Validation protects three properties:

1. deterministic credit decisioning;
2. complete and traceable evidence;
3. bounded, resilient reporting.

> **LLM output is never the source of truth for the credit assessment.**

## Validation Levels

| Level | Scope |
|---|---|
| Unit | Rules, models, validators, services and policies |
| Integration | Cross-layer evidence and case aggregation |
| Workflow | Assessment → analysis → reporting propagation |
| Reporting | Prompt contract, grounding and fallback |
| Scenario | End-to-end domain/rule coverage |
| UI | Read-only presentation boundary |
| CI | Ruff, Mypy and Pytest/coverage |

## Rule Coverage

The configured inventory contains **18 rules**:

| Domain | Rules | Count |
|---|---|---:|
| Customer Profile | `CP001–CP004` | 4 |
| Financial Analysis | `R001–R007` | 7 |
| Behavioural Analysis | `B001–B004` | 4 |
| Debt Sustainability | `DS001–DS003` | 3 |

Tests cover rule registration/discovery, configuration loading, thresholds, severity, boundary conditions and `NOT_EVALUABLE` inputs.

Deterministic invariant:

```text
Same Input + Same Configuration
              ↓
        Same RuleResult
```

## Status Validation

For rule-based sections:

| Condition | Status |
|---|---|
| 2+ `TRIGGERED` | `CRITICAL` |
| 1 `TRIGGERED` | `ATTENTION` |
| 0 triggered + evaluable evidence | `NORMAL` |
| All `NOT_EVALUABLE` | `ATTENTION` |
| Empty result set | `NORMAL` |

At case level:

```text
Any CRITICAL section       → CRITICAL
2+ core ATTENTION sections → CRITICAL
1 core ATTENTION section   → ATTENTION
All evaluable NORMAL       → NORMAL
No evaluable sections      → ATTENTION
```

Customer Profile is contextual for the two-core-area escalation: `ATTENTION` does not count toward that threshold, while `CRITICAL` can still produce `CRITICAL`.

## Workflow Invariant

```text
Input
 ↓
Validation
 ↓
Four Domain Assessments
 ↓
CreditAssessmentCase
 ↓
Final Assessment
 ↓
Deterministic Analysis
 ↓
Reporting
```

Reporting consumes the deterministic result; it does not recreate or modify it.

## Reporting Validation

Tests verify that:

- all four domains reach `AssessmentAnalysis`;
- `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE` are preserved;
- `risk_factors` contains only high-severity triggered evidence;
- the prompt receives the complete evidence set;
- material indicators are preserved when grounding is required;
- provider or grounding failure activates deterministic fallback;
- fallback failure is propagated rather than silently hidden.

The Executive Narrative follows the fixed application-controlled order:

1. Customer Profile
2. Financial Analysis
3. Behavioural Analysis
4. Debt Sustainability

## Scenario Coverage

Demonstration scenarios use synthetic/anonymized data and exercise the four assessment domains and configured rule inventory, including Customer Profile forborne exposure. Scenario tests complement, but do not replace, individual rule tests.

## UI Boundary

The Results hierarchy is:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
```

The UI renders workflow evidence and does not recalculate thresholds, severity or assessment status.

## Execution Metadata

`ExecutionMetadata` is provenance only. Tests verify execution identity, UTC timestamp, reporting mode, generator/fallback state, error classification and timing consistency. Metadata does not participate in decisioning.

## CI Gates

GitHub Actions targets **Python 3.14**:

```text
Install dependencies
        ↓
Ruff
        ↓
Mypy
        ↓
Pytest + coverage
```

The coverage threshold is **95% for `src`**.

## Validation Philosophy

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
