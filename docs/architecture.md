# Architecture

## 1. Overview

The **Credit Assessment System** is a deterministic, rule-based credit assessment application with an optional AI-assisted reporting layer.

The architecture models an analyst-style review across four explicit domains:

1. Customer Profile
2. Financial Analysis
3. Behavioural Analysis
4. Debt Sustainability

The four domains are consolidated into a deterministic `CreditAssessmentCase` and final assessment before narrative reporting.

> **Deterministic evidence is the source of truth. The LLM is optional narrative synthesis and has no decision authority.**

Framework-independent logic lives under `src/`; Streamlit presentation and application orchestration remain under `app/`.

---

## 2. System Architecture

```text
CreditPosition + Case Inputs
          ↓
Structural Validation
          ↓
Assessment Workflow
   ┌──────┼──────────┬──────────────┐
   ↓      ↓          ↓              ↓
Customer Financial Behavioural  Debt Sustainability
Profile  Analysis  Analysis      Analysis
CP001-3  R001-7    B001-4        DS001-3
   └──────┼──────────┴──────────────┘
          ↓
CreditAssessmentCase
          ↓
FinalAssessmentService
          ↓
Final Assessment
          ↓
Deterministic Analysis
          ↓
Reporting Agent
      ┌───┴─────────────┐
      ↓                 ↓
Deterministic       Optional LLM
Generator           Generator
      └───────┬─────────┘
              ↓
            Report
              ↓
      Execution Metadata
```

Dependency direction:

```text
Streamlit / app
      ↓
Workflow / orchestration
      ↓
Services
      ↓
Rules / domain models
      ↓
Configuration
```

The core domain does not depend on Streamlit.

---

## 3. Domain Case Structure

The configured inventory contains **17 rules**:

| Domain | Rules | Count |
|---|---|---:|
| Customer Profile | `CP001–CP003` | 3 |
| Financial Analysis | `R001–R007` | 7 |
| Behavioural Analysis | `B001–B004` | 4 |
| Debt Sustainability | `DS001–DS003` | 3 |

Canonical presentation order:

```text
Customer Profile
Financial Analysis
Behavioural Analysis
Debt Sustainability
```

Each `AssessmentSection` exposes deterministic status, evidence, findings and limitations where applicable. `NOT_EVALUABLE` is explicit and is not silently converted into `NORMAL`.

---

## 4. Domain Responsibilities

### Customer Profile

`CustomerProfileAssessmentService` evaluates `CP001–CP003` for active EWS, restructuring history and business history.

Customer Profile is contextual for the two-core-area final escalation: `ATTENTION` does not count toward that threshold, while `CRITICAL` can still produce a `CRITICAL` final assessment.

### Financial Analysis

The financial domain uses the deterministic Rule Engine for `R001–R007`, covering growth, profitability, leverage, interest burden and related financial indicators.

### Behavioural Analysis

`BehaviouralAssessmentService` evaluates `B001–B004` for utilization, overdraft duration, payment delays and exposure growth.

### Debt Sustainability

`DebtSustainabilityAssessmentService` evaluates `DS001–DS003` using cash-flow and debt-service indicators such as CFADS, debt service and debt-service buffer.

The non-financial domains own their evidence and cannot modify financial rule results.

---

## 5. Deterministic Status Policy

For rule-based sections:

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

An empty result collection remains `NORMAL` for backward-compatible service behaviour.

At case level:

```text
Any CRITICAL section       → CRITICAL
2+ core ATTENTION sections → CRITICAL
1 ATTENTION section        → ATTENTION
All evaluable NORMAL       → NORMAL
No evaluable sections      → ATTENTION
```

No averaging, weighted score or LLM judgement is used.

---

## 6. Validation and Decision Boundary

`CreditPositionValidator` runs before deterministic rule evaluation. It validates expected object type, non-empty identifier, numeric fields, boolean misuse and finite numeric values. `None` remains valid so downstream rules can explicitly return `NOT_EVALUABLE`.

Decision path:

```text
CreditPosition
      ↓
CreditPositionValidator
      ↓
Domain Assessment Services
      ↓
Rule Results / Assessment Sections
      ↓
FinalAssessmentService
      ↓
Final Assessment
```

No LLM participates in this decision path.

---

## 7. Reporting and LLM Boundary

Reporting consumes structured deterministic evidence after assessment and analysis have completed.

The LLM cannot change:

- final status;
- section status;
- rule result;
- severity;
- threshold;
- finding collection;
- limitations.

Python controls the Executive Narrative titles and canonical macro-area order. Gemini/Ollama provide prose synthesis only.

### Provider configuration

Current conservative generation settings:

```text
Gemini: temperature=0.1
        thinking=MINIMAL
        include_thoughts=false
        max_output_tokens=8192

Ollama: temperature=0.2
        think=false
```

These settings affect narrative generation only.

### Grounding and fallback

```text
Deterministic findings
        ↓
Primary generator
        ↓
Grounding validation
     /       \
  valid     invalid/failure
    ↓          ↓
 Narrative  Deterministic fallback
```

Provider failure, invalid output or grounding failure can change the reporting path but never the deterministic assessment.

---

## 8. Results UI Architecture

The current Results page intentionally has a compact hierarchy:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
```

### Executive Credit Assessment

The page begins with the final deterministic status and three compact KPIs: rules evaluated, triggered and not evaluable. Reporting provenance is lightweight metadata only.

### Assessment by Macro-Area

The four `AssessmentSection` objects are the authoritative visible deterministic overview. Each area shows status, evidence counts and relevant indicators.

The dashboard also exposes technical inspection on demand through:

```text
Rule Catalogue & Filters
          ↓
Individual Rule Detail
```

Redundant aggregate charts have been removed.

### Executive Narrative

The Executive Narrative is management-oriented prose generated from deterministic evidence. The visible title is application-controlled and the macro-area order is fixed:

```text
Customer Profile
Financial Analysis
Behavioural Analysis
Debt Sustainability
```

### Removed secondary sections

The current Results page does not render separate bottom-of-page **Risk Drivers** or **Detailed Assessment** sections. Their removal is deliberate: deterministic macro-area evidence is already visible in the authoritative dashboard, while technical inspection is progressively disclosed within that dashboard.

The UI is presentation-only and does not recalculate thresholds, severity or assessment status.

---

## 9. Demo Data Flow

`app/demo_scenarios.py` provides a predefined synthetic **Complete Credit Assessment** scenario:

```text
CreditPosition
   + CustomerProfileData
   + BehaviouralData
   + DebtSustainabilityData
          ↓
Assessment Workflow
          ↓
17-rule multi-domain evidence
```

The scenario populates all four assessment domains. No production banking data is required.

---

## 10. Configuration Architecture

```text
config/
├── customer_profile_rules.yaml
├── financial_analysis_rules.yaml
├── behavioural_analysis_rules.yaml
├── debt_sustainability_rules.yaml
└── final_assessment.yaml
```

Thresholds, severity and aggregation policy are externalized and reviewable. Domain services remain responsible for business semantics and calculations.

---

## 11. Execution Observability

Successful workflows expose immutable `ExecutionMetadata`, including execution identity, UTC timestamp, reporting mode, generator/fallback state, error category where applicable and phase timings.

Observability is outside the decision path:

```text
Assessment Decision  ──X──> Execution Metadata
Execution Metadata   ──X──> Assessment Decision
```

Current execution metadata is workflow-level provenance rather than a persistent audit trail.

---

## 12. CI and Quality Boundary

GitHub Actions validates Python **3.13 and 3.14** through:

```text
Ruff
  ↓
Mypy
  ↓
Pytest + coverage ≥ 95% for src
```

The test suite protects both implementation behaviour and the architectural boundary between deterministic decisioning and optional AI reporting.

---

## 13. Current Architecture Baseline

The current implementation is the thesis-ready multi-domain baseline: 17 configured rules across four explicit domains, deterministic final aggregation, integrated synthetic demo data, a compact evidence-oriented Results UI and bounded optional LLM reporting.

The intended flow is:

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
