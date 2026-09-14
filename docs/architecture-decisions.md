# Architecture Decisions

This document records the decisions that define the current system architecture.

| ID | Decision | Status |
|---|---|---|
| ADR-001 | Deterministic decision authority | Accepted |
| ADR-002 | Separate decision and reporting layers | Accepted |
| ADR-003 | Externalized rule configuration | Accepted |
| ADR-004 | Pluggable rule discovery | Accepted |
| ADR-005 | Provider-agnostic LLM abstraction | Accepted |
| ADR-006 | Deterministic reporting fallback | Accepted |
| ADR-007 | Immutable domain models where appropriate | Accepted |
| ADR-008 | Thin presentation layer | Accepted |
| ADR-009 | Execution provenance | Accepted |
| ADR-010 | Grounded LLM narrative contract | Accepted |
| ADR-011 | Evidence-oriented Results UI | Accepted |
| ADR-012 | Structural input validation | Accepted |
| ADR-013 | Explicit all-`NOT_EVALUABLE` handling | Accepted |
| ADR-014 | Multi-domain case assessment | Accepted |
| ADR-015 | Standalone Risk Drivers presentation | Superseded |
| ADR-016 | Application-controlled Executive Narrative | Accepted |
| ADR-017 | Compact macro-area Results experience | Accepted |

## ADR-001 — Deterministic Decision Authority

Deterministic assessment services own the credit decision. `FinalAssessmentService` performs cross-domain case aggregation. LLM components cannot modify or override structured assessment results.

**Why:** reproducibility, traceability and separation of credit policy from generative AI.

## ADR-002 — Separate Decision and Reporting Layers

Assessment, deterministic analysis and reporting are separate stages. Reporting consumes structured evidence instead of accessing rule logic directly.

**Why:** clear responsibilities and independent testing.

## ADR-003 — Externalized Rule Configuration

Rule parameters such as thresholds, severity and severity direction are externalized under `config/`.

**Why:** policy changes remain reviewable without changing central services.

## ADR-004 — Pluggable Rule Discovery

Rules share common abstractions and are resolved through discovery/registry mechanisms using configured rule identifiers.

**Why:** new indicators do not require rule-specific branching in central services.

## ADR-005 — Provider-Agnostic LLM Abstraction

LLM access is exposed through a common client abstraction with provider-specific implementations such as Gemini, Ollama and mock clients.

**Why:** provider portability and infrastructure isolation.

## ADR-006 — Deterministic Reporting Fallback

Reporting falls back to a deterministic generator when the primary LLM path fails or required grounding fails.

**Why:** AI is optional and must never become a dependency of credit assessment.

## ADR-007 — Immutable Domain Models

Core assessment, analysis, report and execution-state objects use immutable structures where appropriate.

**Why:** downstream components must not silently mutate deterministic facts.

## ADR-008 — Thin Presentation Layer

`app/` owns presentation and application orchestration. Business rules, assessment calculations, models and LLM abstractions remain in `src/`.

**Why:** the core remains reusable and testable outside Streamlit.

## ADR-009 — Execution Provenance

Workflow executions expose immutable metadata such as execution ID, UTC timestamp, reporting mode, generator/fallback state, error category and timings.

**Why:** traceability without making observability part of decisioning.

## ADR-010 — Grounded LLM Narrative Contract

LLM reporting must preserve supplied material findings and numerical evidence, avoid unsupported claims and never generate the structured assessment status.

**Why:** generative output remains bounded by deterministic evidence.

## ADR-011 — Evidence-Oriented Results UI

The Results view centres on one authoritative deterministic macro-area dashboard, followed by the Executive Narrative. Technical rule inspection is progressively disclosed inside the dashboard.

**Why:** avoid duplicated evidence and keep the analyst workflow focused.

## ADR-012 — Structural Input Validation

`CreditPositionValidator` runs before deterministic assessment and validates object type, identifiers, numeric fields, boolean misuse and finite numeric values. `None` remains valid for downstream `NOT_EVALUABLE` handling.

**Why:** separate structural integrity from credit-policy semantics.

## ADR-013 — Explicit All-`NOT_EVALUABLE` Handling

A section where all configured rules are `NOT_EVALUABLE` is `ATTENTION`. An empty result collection remains `NORMAL`.

```text
2+ TRIGGERED                    → CRITICAL
1 TRIGGERED                     → ATTENTION
0 TRIGGERED + evaluable         → NORMAL
ALL NOT_EVALUABLE               → ATTENTION
EMPTY RESULTS                   → NORMAL
```

**Why:** lack of evidence must not be confused with evidence of normality.

## ADR-014 — Multi-Domain Case Assessment

The system models four deterministic domains:

```text
Customer Profile      → CP001–CP003
Financial Analysis    → R001–R007
Behavioural Analysis  → B001–B004
Debt Sustainability   → DS001–DS003
                         ↓
                  Final Assessment
```

Each domain owns its inputs and rule evaluation; `FinalAssessmentService` performs deterministic consolidation.

**Why:** the model reflects an analyst-oriented credit review and keeps rule families separated.

## ADR-015 — Standalone Risk Drivers Presentation

**Superseded.** The former standalone Risk Drivers section was removed because the macro-area dashboard already exposes the authoritative deterministic evidence.

**Why superseded:** avoid duplicate presentation of the same evidence.

## ADR-016 — Application-Controlled Executive Narrative

The Executive Narrative always uses this order:

1. Customer Profile
2. Financial Analysis
3. Behavioural Analysis
4. Debt Sustainability

Python controls titles and order; the LLM supplies prose only.

**Why:** the domain taxonomy is part of the application contract and must not drift between providers.

## ADR-017 — Compact Macro-Area Results Experience

The visible Results hierarchy is:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
```

Rule Catalogue & Filters and Individual Rule Detail are disclosed within the macro-area dashboard. Separate bottom-of-page Risk Drivers and Detailed Assessment sections are not rendered.

**Why:** one authoritative evidence surface is clearer and avoids repeated information.

## Architectural Principles

1. Deterministic logic owns credit decisions.
2. Input integrity is validated before assessment.
3. Four assessment domains remain explicit.
4. `NOT_EVALUABLE` is distinct from `NOT_TRIGGERED`.
5. Rule policy is configuration-driven.
6. Components communicate through structured domain objects.
7. LLM providers remain replaceable.
8. AI is limited to narrative reporting.
9. LLM failure cannot invalidate the assessment.
10. Presentation code does not own business logic.
11. Execution metadata is observational.
12. The Results UI has one authoritative macro-area evidence surface.
