# Architecture

## 1. Overview

The **Credit Assessment System** is a deterministic, rule-based credit assessment application with an optional AI-assisted reporting layer.

The architecture is organized around a higher-level case assessment that mirrors an analyst-style credit review:

1. Customer Profile
2. Financial Analysis
3. Behavioural Analysis
4. Debt Sustainability
5. Final Assessment
6. Executive Synthesis / Reporting

The central boundary is:

> **Deterministic evidence is the source of truth. The LLM is an optional synthesis component and has no decision authority.**

Framework-independent logic lives under `src/`; Streamlit presentation and application orchestration remain under `app/`.

---

## 2. System Architecture

```text
CreditPosition + Case Inputs
          │
          ▼
Assessment Workflow
          │
          ├── CreditPositionValidator
          │
          ├── Customer Profile Service
          │      └── CP001–CP002
          │
          ├── Financial Assessment Service
          │      └── Rule Engine → R001–R007
          │
          ├── Behavioural Assessment Service
          │      └── B001–B004
          │
          └── Debt Sustainability Service
                 └── DS001–DS003
          │
          ▼
Credit Assessment Case
          │
          ▼
FinalAssessmentService
          │
          ▼
Final Assessment
          │
          ├──────────────► Results / Evidence UI
          │
          ▼
Deterministic Analysis
          │
          ▼
Reporting Agent
      ┌───┴─────────────┐
      ▼                 ▼
Deterministic       Optional LLM
Generator           Generator
      │                 │
      └───────┬─────────┘
              ▼
            Report
              │
              ▼
      Execution Metadata
```

### Dependency direction

```text
Streamlit / application (`app/`)
              ↓
        Workflow / orchestration
              ↓
             Services
              ↓
        Rules / domain models
              ↓
        Configuration / data
```

The core domain does not depend on Streamlit.

---

## 3. Domain Case Structure

The case layer composes the independent assessment domains into a single analyst-oriented object.

```text
CreditAssessmentCase
│
├── Customer Profile
├── Financial Analysis
├── Behavioural Analysis
├── Debt Sustainability
└── Final Assessment
```

Each section exposes structured deterministic status, findings, evidence and limitations where applicable.

`NOT_EVALUABLE` explicitly represents missing or insufficient evidence. It is not silently converted into `NORMAL`.

---

## 4. Customer Profile

`CustomerProfileData` contains contextual customer and relationship information, including company identity, legal form, sector, size class, geography, shareholders, management, relationship duration, historical facilities, active EWS and previous restructuring.

`CustomerProfileAssessmentService` evaluates the configured profile flags:

```text
CP001 — Active EWS
CP002 — Previous Restructuring
```

The profile is contextual for final aggregation: an `ATTENTION` profile does not count toward the two-core-area escalation, while a `CRITICAL` profile can still make the final assessment `CRITICAL`.

---

## 5. Financial Analysis

The financial domain uses the seven configured deterministic rules in `config/financial_analysis_rules.yaml`:

```text
Financial Analysis
│
├── Revenue & Growth
│   └── R001 Revenue growth deterioration
├── Profitability
│   ├── R002 Negative EBITDA
│   └── R003 EBITDA margin deterioration
├── Financial Structure
│   └── R004 NFP / EBITDA leverage
├── Debt Service Burden
│   ├── R005 Interest expense / EBITDA
│   └── R007 Interest coverage ratio
└── Profitability Quality
    └── R006 Finished-goods inventory increase / EBITDA
```

The case layer groups the existing deterministic results; it does not duplicate rule evaluation logic.

---

## 6. Behavioural Analysis

`BehaviouralData` provides synthetic banking-behaviour inputs. The behavioural service evaluates B001–B004 for:

- average utilization;
- overdraft duration;
- payment delays;
- exposure growth.

Behavioural assessment is independent from the financial rule engine and cannot modify financial rule results.

---

## 7. Debt Sustainability

`DebtSustainabilityData` provides cash-flow and debt-service inputs. The service evaluates:

```text
DS001 — Debt Service Coverage Ratio
        CFADS / Debt Service

DS002 — Debt Service / EBITDA
        Debt Service / EBITDA

DS003 — Cash Flow Debt-Service Buffer
        CFADS − Debt Service
```

These indicators deliberately address debt-service sustainability without duplicating the existing financial rules R004, R005 and R007.

---

## 8. Deterministic Status Policy

For a rule-based section, status is derived from deterministic rule results:

```text
2+ TRIGGERED
      ↓
   CRITICAL

1 TRIGGERED
      ↓
  ATTENTION

0 TRIGGERED + at least one evaluable rule
      ↓
   NORMAL

ALL NOT_EVALUABLE
      ↓
  ATTENTION
```

An empty rule-result collection remains `NORMAL` for backward-compatible service behaviour and is distinct from a configured assessment in which every rule is non-evaluable.

---

## 9. Final Aggregation

`FinalAssessmentService` combines section-level statuses through an explicit deterministic policy:

```text
Any CRITICAL section       → CRITICAL
2+ core ATTENTION sections → CRITICAL
1 ATTENTION section        → ATTENTION
All evaluable NORMAL       → NORMAL
No evaluable sections      → ATTENTION
```

No averaging, weighted score or LLM judgement is used.

`NOT_EVALUABLE` sections are excluded from positive/negative status counts but remain visible as evidence limitations.

---

## 10. Validation and Decision Boundary

`CreditPositionValidator` performs structural validation before financial rule evaluation. It checks the expected `CreditPosition` type, non-empty identifier, numeric field types, boolean misuse and finite numeric values. `None` remains valid so downstream rules can explicitly return `NOT_EVALUABLE`.

The validator does not enforce generic financial sign constraints; economic semantics belong to the corresponding rule.

The financial decision path is:

```text
CreditPosition
      ↓
CreditPositionValidator
      ↓
AssessmentService
      ↓
RuleEngine
      ↓
RuleResult[]
      ↓
CommentEngine / StatusCalculator
      ↓
Assessment
```

No LLM participates in this path.

---

## 11. Workflow and Reporting Boundary

The application workflow composes deterministic case assessment and reporting.

```text
Input
 ↓
Validation
 ↓
Domain assessments
 ↓
CreditAssessmentCase
 ↓
FinalAssessment
 ↓
Deterministic analysis
 ↓
Reporting
 ├── deterministic generator
 └── optional LLM generator
        ↓
   grounding / resilience checks
        ↓
   deterministic fallback when required
        ↓
      Report
```

The reporting layer consumes structured assessment evidence. LLM output cannot change:

- final status;
- section status;
- rule result;
- severity;
- threshold;
- finding collection;
- limitations.

---

## 12. LLM Provider Abstraction

LLM access is provider-agnostic through the `LLMClient` abstraction.

```text
Reporting Generator
        ↓
     LLMClient
     /       \
 Gemini      Ollama
```

A mock client is available for deterministic testing. Provider failures are classified and can activate deterministic reporting fallback.

---

## 13. Grounding and Resilience

When strict indicator grounding is enabled:

```text
Deterministic findings
        ↓
Required indicator values
        ↓
LLM narrative
        ↓
Grounding validation
     /       \
  valid     invalid
    ↓          ↓
 Narrative  Deterministic fallback
```

The grounding control is intentionally narrow: it protects required deterministic numerical evidence and is not presented as a full semantic fact-checker.

The key invariant is:

> **LLM failure or invalid grounding can change the reporting path, but never the deterministic assessment.**

---

## 14. Results UI Architecture

The Streamlit Results experience uses progressive disclosure:

```text
Executive Credit Assessment
          ↓
Final Assessment
          ↓
Risk Drivers
          ↓
Rule Engine Evidence
          ↓
Executive Narrative
          ↓
Detailed Analysis by Macro-area
```

### Executive Credit Assessment

Primary decision surface showing the deterministic final status and compact assessment KPIs.

### Final Assessment

Shows deterministic macro-area consolidation and explicit limitations without duplicating the executive summary.

### Risk Drivers

Shows triggered deterministic indicators across assessment domains, ordered by configured severity priority. This is an evidence-ranking view, not a new risk score.

### Rule Engine Evidence

Shows rule-outcome and severity distributions, a filterable rule catalogue and individual rule details. Technical inspection is progressively disclosed.

### Executive Narrative

Shows management-oriented reporting generated from deterministic evidence. The narrative is not the source of the displayed status.

### Detailed Analysis

Provides deeper macro-area evidence and data-quality information for analyst drill-down.

All visualizations consume workflow outputs. The UI does not recalculate thresholds, severity or assessment status.

---

## 15. Demo Data Flow

The repository contains a predefined synthetic scenario in `app/demo_scenarios.py`:

```text
Complete Credit Assessment
        ↓
CreditPosition
        +
CustomerProfileData
        +
BehaviouralData
        +
DebtSustainabilityData
        ↓
Assessment Workflow
```

The scenario intentionally populates all assessment domains so the application can demonstrate the complete configured rule inventory in one end-to-end execution.

No production banking data is required for the demo.

---

## 16. Configuration Architecture

Rule and aggregation policy is externalized under `config/`:

```text
config/
├── financial_analysis_rules.yaml
├── behavioural_analysis_rules.yaml
├── debt_sustainability_rules.yaml
├── customer_profile_rules.yaml
└── final_assessment.yaml
```

This separates rule parameters and policy from application presentation and keeps configuration reviewable and reproducible.

---

## 17. Execution Observability

Successful workflow executions expose immutable `ExecutionMetadata`, including execution identity, UTC timestamp, reporting mode, generator/fallback state, error category when applicable and phase timings.

Observability is intentionally outside the decision path:

```text
Assessment Decision  ──X──> Execution Metadata
Execution Metadata   ──X──> Assessment Decision
```

Current execution metadata is workflow-level provenance rather than a persistent audit trail.

---

## 18. CI and Quality Boundary

The GitHub Actions workflow targets Python **3.13 and 3.14** and runs:

```text
Install dependencies
        ↓
Ruff
        ↓
Mypy
        ↓
Pytest + coverage ≥ 95% for src
```

CI therefore validates both implementation quality and the deterministic architectural contracts represented by the test suite.

---

## 19. Current Architecture Baseline

The current implementation includes the completed multi-domain case structure, integrated demo data flow, deterministic final aggregation, evidence-oriented Results UI and the simplified Risk Drivers presentation.

Recent UI refactoring removed threshold-distance presentation and related helpers. Risk Drivers now ranks triggered evidence by deterministic severity priority rather than exposing a derived threshold-distance metric.

The architecture intentionally remains:

```text
Deterministic Core
      ↓
Structured Evidence
      ↓
Final Assessment
      ↓
Optional Narrative Synthesis
```

AI remains optional, replaceable and non-decisional.
