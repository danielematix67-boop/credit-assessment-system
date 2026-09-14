# Credit Assessment System

> Deterministic, multi-domain credit-risk assessment with controlled AI-assisted reporting.

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Testing](https://img.shields.io/badge/Tested_with-pytest-0A9EDC?logo=pytest)](https://pytest.org/)
[![Linting](https://img.shields.io/badge/Linting-ruff-D7FF64)](https://docs.astral.sh/ruff/)

## Overview

**Credit Assessment System** evaluates a synthetic credit position through explicit, configurable rules across four assessment domains and presents the resulting evidence through Streamlit.

> **The deterministic system decides; AI explains.**

Decisioning, analysis, reporting and presentation are separate concerns. Gemini and local Ollama are optional reporting providers and cannot change status, thresholds, severity, findings, limitations or the final decision.

## Assessment Model

The current catalogue contains **18 rules across four domains**:

| Domain | Rule IDs | Count |
|---|---|---:|
| Customer Profile | `CP001–CP004` | 4 |
| Financial Analysis | `R001–R007` | 7 |
| Behavioural Analysis | `B001–B004` | 4 |
| Debt Sustainability | `DS001–DS003` | 3 |

Canonical order: **Customer Profile → Financial Analysis → Behavioural Analysis → Debt Sustainability**.

For rule-based sections:

| Condition | Status |
|---|---|
| 2+ triggered rules | `CRITICAL` |
| Exactly 1 triggered rule | `ATTENTION` |
| No triggered rules + evaluable evidence | `NORMAL` |
| All rules `NOT_EVALUABLE` | `ATTENTION` |
| Empty result set | `NORMAL` |

At case level, `CRITICAL` propagates directly; two or more core `ATTENTION` sections escalate to `CRITICAL`; one core `ATTENTION` produces `ATTENTION`; otherwise the case is `NORMAL`. If no section is evaluable, the case is `ATTENTION`.

Customer Profile is contextual for the two-core-area escalation: `ATTENTION` does not count toward that threshold, while `CRITICAL` can still produce a `CRITICAL` case.

`NOT_EVALUABLE` is distinct from `NOT_TRIGGERED`.

## Architecture

```text
CreditPosition
     ↓
Input Validation
     ↓
Four Domain Assessments
     ↓
CreditAssessmentCase
     ↓
Final Assessment
     ↓
Deterministic Analysis
     ↓
Reporting Agent
   ↙       ↘
Deterministic  Optional LLM
 Generator     Gemini / Ollama
      ↘       ↙
        Report
```

The core implementation is under `src/`; Streamlit presentation and application orchestration are under `app/`.

## Configuration

Rules are configured by domain under `config/`:

```text
config/
├── customer_profile_rules.yaml
├── financial_analysis_rules.yaml
├── behavioural_analysis_rules.yaml
├── debt_sustainability_rules.yaml
└── final_assessment.yaml
```

Thresholds, severity and severity direction are configuration-driven. Rule and domain implementations contain the corresponding business semantics.

## Adding a New Rule

Adding a rule must update the **complete deterministic evidence path**, not only the YAML catalogue:

```text
Business definition
      ↓
CreditPosition input field(s)
      ↓
config/<domain>_rules.yaml
      ↓
src/rules/<domain>/<rule_id>.py
      ↓
Automatic discovery + shared registry
      ↓
Domain assessment / RuleEngine
      ↓
RuleResult
      ↓
Deterministic analysis
      ↓
Reporting + grounding validation
      ↓
Results UI
      ↓
Tests + demo data + documentation
```

### 1. Define the business rule

Specify before coding:

- **Rule ID**: unique and stable (`CPxxx`, `Rxxx`, `Bxxx`, `DSxxx`).
- **Domain**: Customer Profile, Financial Analysis, Behavioural Analysis or Debt Sustainability.
- **Business meaning**: the credit-risk condition detected and its rationale.
- **Input field(s)**: data required for evaluation.
- **Calculation**: `direct`, `ratio` or `difference`, when generic support is sufficient.
- **Trigger operator**: `GT`, `GTE`, `LT` or `LTE`.
- **Threshold**: trigger boundary.
- **Severity**: `LOW`, `MEDIUM` or `HIGH`.
- **Severity direction**: `HIGHER_IS_WORSE` or `LOWER_IS_WORSE`.
- **Severity bands**: optional `severity_thresholds` for additional severity boundaries.
- **Comment**: deterministic evidence text via `comment_template`.
- **Non-evaluable conditions**: when the rule cannot be assessed reliably.

The expected behaviour must be explicit for **triggered**, **not triggered** and **not evaluable** cases.

### 2. Add the required input to `CreditPosition`

If a new field is required, add it to the appropriate position model and ensure its type and structural validation are correct.

```python
revenue_growth: float | None
previous_restructuring: bool | None
```

Use `None` when missing information must remain distinguishable from a valid value. Missing or invalid evidence should normally result in `NOT_EVALUABLE`, not an implicit normal value.

### 3. Add the YAML configuration

Add the rule to the YAML catalogue for its domain, for example:

```yaml
- rule_id: R008
  rule_name: Example deterioration rule
  indicator: Example indicator
  category: profitability
  input_field: example_value
  trigger_operator: LT
  threshold: 0.0
  severity: MEDIUM
  severity_direction: LOWER_IS_WORSE
  severity_thresholds:
    - threshold: 0.0
      severity: MEDIUM
    - threshold: -0.10
      severity: HIGH
  comment_template: >-
    Example indicator stands at {value:.1%}, indicating deterioration.
```

The loader validates required fields, duplicate IDs, thresholds, operators, calculation types, severity values, severity directions and severity bands. Supported calculations are `direct`, `ratio` and `difference`.

For a two-input ratio:

```yaml
input_fields:
  - numerator_field
  - denominator_field
calculation: ratio
```

The generic base rule handles missing inputs and prevents division by zero. Use specialised Python logic when the business semantics require it.

### 4. Implement the deterministic rule

Create **one Python module per concrete rule**:

```text
src/rules/<domain>/<rule_id_lowercase>.py
```

The implementation inherits from `Rule` and registers itself with the exact configured ID:

```python
from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("R008")
class ExampleRule(Rule):
    def evaluate(self, position) -> RuleResult:
        value, error = self._configured_value(position)
        if error is not None or value is None:
            return self._not_evaluable(
                error or "Required evidence is unavailable."
            )

        status = (
            RuleStatus.TRIGGERED
            if self._is_triggered(value)
            else RuleStatus.NOT_TRIGGERED
        )
        return self._result(value=value, status=status)
```

For specialised rules, override `evaluate()` and use the base helpers where appropriate: `_configured_value`, `_is_triggered`, `_severity`, `_result` and `_not_evaluable`.

Keep credit-risk semantics in the rule implementation. Do **not** put rule logic in the `RuleEngine`, Streamlit or LLM layer.

**No central import list is required.** `discover_rules()` recursively imports rule modules under `src.rules`, while `build_rules()` resolves each configured `rule_id` through the shared registry. The implementation therefore only needs to exist and register correctly.

### 5. Verify registration and configuration consistency

The architectural invariant is:

```text
Every configured rule_id
        ↓
one concrete registered Rule implementation
        ↓
deterministic RuleResult
```

A missing implementation, duplicate ID or invalid configuration must fail validation rather than silently dropping the rule.

### 6. Add rule-specific tests

Mirror the source structure under `tests/rules/`:

```text
tests/rules/<domain>/test_<rule_id_lowercase>.py
```

At minimum cover:

1. **Triggered** behaviour.
2. **Not triggered** behaviour.
3. **Boundary** behaviour, especially `GT` vs `GTE` and `LT` vs `LTE`.
4. **Severity**, including every configured severity band.
5. **Missing input** → `NOT_EVALUABLE`.
6. **Invalid input** handling.
7. **Calculation edge cases**, especially zero denominators for ratios.
8. **Evidence**, including rule ID, value, threshold, status, severity and reason.

Also update configuration/registry tests when the catalogue or discovery contract changes.

### 7. Verify domain and final aggregation

A new rule can change the number of triggered rules and therefore the domain and case status:

```text
RuleResult
   ↓
Domain status
   ↓
Final case status
```

Check whether the rule changes `NORMAL`, `ATTENTION` or `CRITICAL`, and whether it affects the core-area escalation policy. Aggregation logic must remain outside the rule.

### 8. Verify deterministic analysis and reporting

The rule must reach the analysis and reporting layers as deterministic evidence. Reporting may explain evidence but must not invent, alter, suppress or reinterpret the deterministic decision.

Check that:

- the rule result reaches deterministic analysis;
- triggered findings are available to reporting;
- high-severity results are handled as risk factors where applicable;
- `NOT_EVALUABLE` remains a limitation rather than normal evidence;
- indicator values used in narrative generation are grounded in deterministic evidence;
- grounding validation rejects unsupported or altered numeric evidence;
- deterministic fallback still produces a valid report if the LLM fails.

No prompt or LLM provider should contain the rule's decision logic.

### 9. Update demo data and UI when necessary

If the rule requires new input data, update synthetic/anonymized demo scenarios so the rule is exercised. Where useful, demonstrate both triggered and non-triggered outcomes.

Streamlit must consume the assessment and rule catalogue; it must not duplicate rule logic or thresholds. Verify that the rule appears in the authoritative macro-area evidence surface and technical rule inspection.

Never commit production or confidential banking data.

### 10. Update documentation and catalogue counts

When adding a rule, update documentation that lists:

- total rule count;
- domain rule ranges/counts;
- rule inventory examples;
- architecture/source-tree examples;
- affected ADRs or validation documentation;
- roadmap/baseline statements that are no longer accurate.

The active catalogue is defined by YAML configuration plus registered deterministic implementations. Documentation must describe `main` as it actually exists.

### 11. Run the complete quality gate

```bash
python -m ruff check .
python -m mypy src
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

A new rule is complete only when configuration, implementation, discovery, deterministic assessment, evidence propagation, tests, demo coverage and documentation are consistent.

## Results UI

The Results page follows a compact hierarchy:

```text
Executive Credit Assessment
          ↓
Assessment by Macro-Area
          ↓
Executive Narrative
```

The macro-area dashboard is the authoritative deterministic evidence surface. Technical inspection is progressively disclosed through **Rule Catalogue & Filters** and **Individual Rule Detail**.

Separate bottom-of-page Risk Drivers and Detailed Assessment sections are not rendered. The UI does not recalculate rules or decisions.

## AI-Assisted Reporting

| Mode | Behaviour |
|---|---|
| **Deterministic** | Model-independent deterministic narrative |
| **Gemini + Fallback** | Gemini narrative with deterministic fallback |
| **Ollama + Fallback** | Local Ollama narrative with deterministic fallback |

The LLM receives deterministic evidence and generates prose only. Grounding validation can reject an invalid narrative and activate deterministic fallback.

```text
Deterministic Evidence
        ↓
Primary Generator
        ↓
Grounding Validation
    ↙           ↘
 valid        invalid/failure
   ↓               ↓
 Report      Deterministic Fallback
```

The Executive Narrative always follows the application-controlled order of the four domains.

## Execution Metadata

Workflow execution metadata records provenance such as execution ID, UTC timestamp, reporting mode, generator/fallback state, error category and timings. It is observational and does not participate in decisioning.

## Demo Data

Demonstration data is synthetic/anonymized and covers the configured assessment domains and rule inventory, including the Customer Profile forborne exposure indicator. Production or confidential banking data must not be committed to the repository.

## Project Structure

```text
credit-assessment-system/
├── app/
│   ├── streamlit_app.py
│   ├── demo_scenarios.py
│   ├── ui/
│   │   ├── input/
│   │   └── results/
│   └── workflow/
├── config/
├── src/
│   ├── agents/
│   ├── comments/
│   ├── config/
│   ├── engine/
│   ├── llm/
│   ├── models/
│   ├── rules/
│   │   ├── base/
│   │   ├── customer_profile/
│   │   ├── financial_analysis/
│   │   ├── behavioural/
│   │   └── sustainability/
│   └── services/
├── docs/
├── tests/
├── requirements.txt
└── README.md
```

Legacy rule trees and compatibility UI/test paths are not part of the current architecture.

## Installation

### Requirements

- Python **3.14**
- Git
- Optional: Ollama for local reporting

```bash
git clone https://github.com/danielematix67-boop/credit-assessment-system.git
cd credit-assessment-system
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app/streamlit_app.py
```

Configure `GEMINI_API_KEY` through an environment variable or Streamlit secrets when Gemini reporting is enabled. Configure Ollama according to the local installation when local reporting is enabled.

## Testing and CI

The test suite mirrors the source architecture and covers rules, models, services, agents, workflow, reporting, application UI and integration boundaries.

GitHub Actions targets **Python 3.14** and runs:

```text
Ruff → Mypy → Pytest + coverage
```

The coverage gate is **95% for `src`**.

Local checks:

```bash
python -m ruff check .
python -m mypy src
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

## Documentation

- [`docs/README.md`](docs/README.md) — documentation map and maintenance rules.
- [`docs/architecture.md`](docs/architecture.md) — current architecture, domains, workflow, configuration and UI.
- [`docs/reporting.md`](docs/reporting.md) — deterministic evidence flow and bounded reporting.
- [`docs/architecture-decisions.md`](docs/architecture-decisions.md) — architectural decisions and rationale.
- [`docs/adr-016-complete-rule-evidence-reporting.md`](docs/adr-016-complete-rule-evidence-reporting.md) — complete rule-evidence propagation into reporting.
- [`docs/adr-017-rule-implementation-configuration-separation.md`](docs/adr-017-rule-implementation-configuration-separation.md) — separation between rule configuration, deterministic implementation and automatic discovery.
- [`docs/validation.md`](docs/validation.md) — validation strategy, testing and CI.
- [`docs/security-data-handling.md`](docs/security-data-handling.md) — security and data-handling principles.

## Design Principles

- **Deterministic decision logic** — rules own the credit judgement.
- **Domain separation** — four assessment domains remain explicit.
- **Configuration over hard-coding** — policy parameters are externalized.
- **Explicit data availability** — `NOT_EVALUABLE` is not normal evidence.
- **Explainability** — rule evidence remains traceable.
- **AI as bounded reporting** — LLMs generate narrative, not decisions.
- **Grounded generation** — narrative is constrained by deterministic evidence.
- **Resilience** — reporting can fall back deterministically.
- **Thin presentation** — Streamlit consumes assessment results rather than implementing credit logic.

## Roadmap

- [x] Deterministic multi-domain assessment
- [x] 18 configured rules across four domains
- [x] Configurable thresholds and severity
- [x] Structural input validation
- [x] Explicit `NOT_EVALUABLE` handling
- [x] Deterministic final aggregation
- [x] Explainable rule evidence
- [x] Compact macro-area Results dashboard
- [x] Application-controlled Executive Narrative
- [x] Gemini integration
- [x] Local Ollama integration
- [x] Deterministic LLM fallback
- [x] LLM grounding validation
- [x] Execution observability
- [x] CI on Python 3.14
- [ ] Persistent assessment history
- [ ] Rule-set versioning and auditability
- [ ] Expanded monitoring/evaluation metrics
- [ ] Additional rule families and external data sources

## Current Baseline

The `main` branch is the current thesis-ready baseline: four deterministic assessment domains, 18 configured rules, deterministic case aggregation, synthetic demonstration data, a compact evidence-oriented Results experience and bounded optional LLM reporting.

The architecture keeps assessment independent from Streamlit and from every LLM provider. The application decides first; reporting explains the resulting evidence afterward.

## Author

**Daniele Ottelli**

Credit Risk · Data Analytics · Python · SQL · Machine Learning · AI
