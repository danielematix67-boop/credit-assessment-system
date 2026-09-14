# Getting Started

This guide is for someone opening the repository for the first time and wanting to understand the project, run it locally and inspect the assessment workflow.

## 1. What you are running

The application evaluates a credit position using a deterministic, configuration-driven Rule Engine.

The high-level flow is:

```text
Credit Position
      ↓
Validation
      ↓
Rule Evaluation
      ↓
Domain Assessment
      ↓
Final Assessment
      ↓
Reporting
      ↓
Streamlit UI
```

The deterministic assessment is authoritative. Optional AI is used only downstream for narrative reporting.

## 2. Clone the repository

```bash
git clone https://github.com/danielematix67-boop/credit-assessment-system.git
cd credit-assessment-system
```

## 3. Create the Python environment

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Use a Python version supported by the repository's CI workflow. The workflow configuration is the authoritative compatibility reference; this guide intentionally does not duplicate a specific runtime version.

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Run the quality checks

Before changing the project, establish a clean baseline using the commands defined by the repository CI:

```bash
python -m ruff check .
python -m mypy src
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

The CI workflow is the authoritative source for the exact quality gates and supported runtime.

## 6. Start the application

```bash
streamlit run app/streamlit_app.py
```

The browser interface is the presentation layer. It should display results produced by the assessment workflow rather than implement credit logic itself.

A hosted demonstration may also be available at:

<https://credit-assessment-system.streamlit.app/>

## 7. Understand the result

When exploring an assessment, follow the evidence in this order:

```text
Credit Position
      ↓
Rule Results
      ↓
Domain Status
      ↓
Overall Assessment
      ↓
Key Findings / Risk Factors / Limitations
      ↓
Executive Narrative
```

Rule results have three explicit states:

- `TRIGGERED` — the configured condition is met.
- `NOT_TRIGGERED` — the rule was evaluated and the condition is not met.
- `NOT_EVALUABLE` — required evidence is unavailable or invalid for evaluation.

`NOT_EVALUABLE` is not equivalent to a normal result.

## 8. Where to look in the repository

| Path | Start here when you want to understand... |
|---|---|
| `app/` | the user interface and application orchestration |
| `config/` | declarative rules and assessment policy |
| `src/rules/` | deterministic rule abstractions and implementations |
| `src/engine/` | rule execution |
| `src/services/` | assessment workflow and aggregation |
| `src/agents/` | analysis and reporting orchestration |
| `src/llm/` | LLM abstraction and reporting providers |
| `tests/` | expected behaviour and regression protection |
| `docs/` | architecture and development guidance |

## 9. Understand how rules are added

Do not start by editing the Streamlit application.

A new rule normally follows this sequence:

```text
Business requirement
        ↓
Input contract
        ↓
YAML configuration
        ↓
Concrete Rule implementation
        ↓
Automatic discovery / registry
        ↓
RuleResult
        ↓
Domain / case aggregation
        ↓
Analysis evidence
        ↓
Reporting and grounding
        ↓
Demo data / UI
        ↓
Tests
```

Read [`rules.md`](rules.md) before implementing a new rule. It contains the complete checklist and explains which responsibilities belong to configuration, rule implementations, services, reporting and tests.

## 10. Understand the AI boundary

The reporting layer can use an LLM, but the LLM does not own:

- indicator calculation;
- threshold evaluation;
- rule severity;
- domain status;
- final credit assessment;
- deterministic evidence.

If the primary reporting path fails or produces output that does not satisfy grounding requirements, the system can use deterministic reporting instead.

This makes the AI component useful without making the credit decision dependent on model behaviour.

## 11. Recommended reading order

For a non-technical reader:

```text
README.md
   ↓
This guide
   ↓
Architecture
   ↓
Reporting
```

For a developer:

```text
Architecture
   ↓
Rules
   ↓
Validation
   ↓
Reporting
   ↓
ADRs
```

For a thesis/reviewer perspective:

```text
Business problem
   ↓
Architecture
   ↓
Deterministic / AI boundary
   ↓
Rule lifecycle
   ↓
Validation and testing
   ↓
Architectural decisions
```

## 12. Contribution checklist

Before submitting a change:

- [ ] The deterministic behaviour is defined before the UI/reporting change.
- [ ] Configuration is used for declarative policy where appropriate.
- [ ] No rule-specific branch was unnecessarily added to central services.
- [ ] `NOT_EVALUABLE` semantics remain explicit.
- [ ] Tests cover the new or changed behaviour.
- [ ] Reporting still consumes deterministic evidence.
- [ ] AI output cannot alter the assessment.
- [ ] Documentation describes the stable contract rather than a temporary implementation detail.
- [ ] Ruff, mypy and pytest pass locally.

## 13. Further documentation

- [`architecture.md`](architecture.md) — system structure and boundaries.
- [`rules.md`](rules.md) — complete rule-development lifecycle.
- [`reporting.md`](reporting.md) — evidence and reporting contract.
- [`validation.md`](validation.md) — validation and quality gates.
- [`security-data-handling.md`](security-data-handling.md) — data and security principles.
- [`architecture-decisions.md`](architecture-decisions.md) — architectural decisions and rationale.
