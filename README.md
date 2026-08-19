# credit-assessment-system

A modular prototype for **credit assessment** built around a **deterministic rule engine**, a structured **analysis layer**, and an optional **LLM-assisted reporting layer**.

The system is deliberately split into two responsibilities that are never allowed to mix:

1. **Credit assessment** — performed exclusively by deterministic business rules and explicit YAML configuration.
2. **Natural-language reporting** — an LLM (or a deterministic fallback) turns an already-validated assessment into an executive summary.

> **The deterministic rule engine is the source of truth. The LLM has no decision-making authority.**
> It cannot determine the assessment status, evaluate rules, change thresholds or severity, create or remove findings, modify limitations, or make an independent credit decision. Its only job is to phrase already-computed, structured information as prose.

This README is derived solely from the code and configuration present in the repository (`src/`, `config/`, `tests/`, `docs/`, `requirements.txt`, `pyproject.toml`).

---

## Table of contents

- [Project overview](#project-overview)
- [Main objectives](#main-objectives)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Deterministic rule engine](#deterministic-rule-engine)
- [Analysis Agent](#analysis-agent)
- [Reporting Agent](#reporting-agent)
- [LLM integration](#llm-integration)
- [Deterministic fallback](#deterministic-fallback)
- [Supported reporting modes](#supported-reporting-modes)
- [Installation](#installation)
- [Environment configuration](#environment-configuration)
- [Running the Streamlit application](#running-the-streamlit-application)
- [Testing](#testing)
- [Ruff / linting](#ruff--linting)
- [Configuration](#configuration)
- [Example workflow](#example-workflow)
- [Design principles](#design-principles)
- [Limitations](#limitations)
- [Future improvements](#future-improvements)

---

## Project overview

`credit-assessment-system` evaluates a structured financial position (`CreditPosition`) against a set of configurable, deterministic credit-risk rules, and produces:

- a machine-readable `Assessment` (rule-by-rule results and an overall status: `NORMAL`, `ATTENTION`, `CRITICAL`);
- a structured `AssessmentAnalysis` (key findings, risk factors, limitations);
- a final `Report`, containing structured findings plus a natural-language executive summary that can be produced either deterministically or with the assistance of an LLM.

The project intentionally operates on **structured domain data**, not free-text financial statements, so that every assessment is reproducible and traceable back to the specific rule and configuration that produced it.

## Main objectives

Based on the implementation and `docs/architecture.md`, the project is designed around the following goals:

- **Determinism** — identical `CreditPosition` + identical rule configuration always produce the identical `Assessment`.
- **Traceability** — every finding in the final report can be traced back through `AssessmentAnalysis` → `Assessment` → `RuleFinding` → `RuleResult` → the originating `Rule`.
- **Separation of decision and reporting** — the credit decision (deterministic) is fully separated from how it is communicated (deterministic text or LLM narrative).
- **Testability** — every component (rules, engine, services, agents, LLM clients) is unit- and integration-testable, with external dependencies isolated behind interfaces.
- **Fault isolation** — a failing or unavailable LLM must never invalidate the deterministic assessment.
- **Provider independence** — the reporting layer depends on an `LLMClient` abstraction, not on a specific vendor SDK.

## Architecture

The processing pipeline, as implemented in `src/`, is:

```text
CreditPosition
      │
      ▼
AssessmentService          (src/services/assessment_service.py)
      │
      ▼
RuleEngine                 (src/engine/rule_engine.py)
      │
      ├── Rule 1 (R001) ── RuleResult
      ├── Rule 2 (R002) ── RuleResult
      ├── ...
      └── Rule N (R007) ── RuleResult
      │
      ▼
RuleResult[]
      │
      ├── AssessmentStatusCalculator   (src/services/assessment_status_calculator.py)
      └── CommentEngine                (src/comments/comment_engine.py)
      │
      ▼
Assessment                 (src/models/assessment.py)
      │
      ▼
AnalysisAgent               (src/agents/analysis/analysis_agent.py)
      │
      ▼
AssessmentAnalysis          (src/models/assessment_analysis.py)
      │
      ▼
ReportingAgent               (src/agents/reporting/reporting_agent.py)
      │
      ├──────────────────────────┐
      ▼                          ▼
LLMReportGenerator        DeterministicReportGenerator
      │                          │
      ▼                          │
   LLMClient                     │
      │                          │
 ┌────┴──────┬───────────┐       │
 ▼           ▼           ▼       │
Gemini    Ollama       Mock      │
      │                          │
      └────────────┬─────────────┘
                   ▼
                 Report            (src/models/report.py)
```

The whole pipeline is coordinated end-to-end by `AssessmentWorkflow` (`src/agents/workflow/assessment_workflow.py`), which is itself exposed to callers through `AssessmentOrchestrator` (`src/orchestration/orchestrator.py`).

Key architectural properties enforced by the code (see `docs/architecture.md` and `docs/validation.md` for the full rationale):

- `RuleEngine` produces exactly one `RuleResult` per configured rule — it never calls an LLM and never generates natural language.
- `AssessmentStatusCalculator` is the *only* component that computes the overall status, from the count of `TRIGGERED` rule results (`NOT_EVALUABLE` results never count as triggered).
- `AnalysisAgent` only *transforms* an existing `Assessment` into an `AssessmentAnalysis` — it does not re-assess anything.
- `ReportingAgent` chooses between a primary `ReportGenerator` and an optional fallback `ReportGenerator`, both of which consume the same `AssessmentAnalysis`.
- `LLMReportGenerator` only ever produces the free-text executive summary; the assessment status, findings, and limitations placed into the final `Report` come directly from the deterministic `AssessmentAnalysis`, not from the LLM.

## Project structure

```text
credit-assessment-system/
├── config/
│   └── rules.yaml                     # Declarative rule configuration (thresholds, severities)
├── docs/
│   ├── architecture.md                # Detailed architecture reference
│   └── validation.md                  # Validation / testing strategy reference
├── src/
│   ├── agents/
│   │   ├── base/agent.py              # Generic Agent[InputT, OutputT] abstract base class
│   │   ├── analysis/analysis_agent.py # AnalysisAgent
│   │   ├── reporting/
│   │   │   ├── report_generator.py            # ReportGenerator abstraction
│   │   │   ├── deterministic_report_generator.py
│   │   │   ├── llm_report_generator.py
│   │   │   └── reporting_agent.py              # ReportingAgent (primary + fallback orchestration)
│   │   └── workflow/
│   │       ├── assessment_workflow.py # AssessmentWorkflow (assess → analyze → report)
│   │       └── workflow_factory.py    # create_default_assessment_workflow()
│   ├── comments/
│   │   ├── comment.py                 # Comment dataclass
│   │   ├── comment_engine.py          # CommentEngine (maps triggered RuleResults to text)
│   │   └── templates.py               # COMMENTS: per-rule human-readable templates
│   ├── config/
│   │   ├── rule_configuration.py      # RuleConfiguration (default rules.yaml path)
│   │   └── rule_config_loader.py      # RuleConfigLoader (YAML -> RuleConfig)
│   ├── engine/
│   │   ├── rule_engine.py             # RuleEngine
│   │   └── finding_engine.py          # FindingEngine
│   ├── llm/
│   │   ├── client.py                  # LLMClient abstract base class
│   │   ├── mock_client.py             # MockLLMClient (deterministic, for tests)
│   │   ├── gemini_client.py           # GeminiClient (Google Gemini API)
│   │   ├── ollama_client.py           # OllamaClient (local Ollama models)
│   │   ├── prompt_template.py         # ReportPromptTemplate (static prompt instructions)
│   │   └── prompt_builder.py          # ReportPromptBuilder (builds the final prompt)
│   ├── models/
│   │   ├── position.py                # CreditPosition
│   │   ├── assessment.py              # Assessment
│   │   ├── assessment_status.py       # AssessmentStatus (NORMAL/ATTENTION/CRITICAL)
│   │   ├── assessment_analysis.py     # AssessmentAnalysis
│   │   ├── assessment_workflow.py     # AssessmentWorkflowResult
│   │   ├── analysis_finding.py        # AnalysisFinding
│   │   ├── rule_finding.py            # RuleFinding
│   │   └── report.py                  # Report, ReportFindingGroup
│   ├── orchestration/
│   │   ├── orchestrator.py            # AssessmentOrchestrator
│   │   └── orchestrator_factory.py    # create_default_orchestrator()
│   ├── rules/
│   │   ├── base/
│   │   │   ├── rule.py                # Rule ABC + registry + severity/result helpers
│   │   │   ├── config.py              # RuleConfig
│   │   │   ├── status.py              # RuleStatus (TRIGGERED/NOT_TRIGGERED/NOT_EVALUABLE)
│   │   │   ├── severity.py            # RuleSeverity (LOW/MEDIUM/HIGH)
│   │   │   ├── severity_direction.py  # SeverityDirection (LOWER_IS_WORSE/HIGHER_IS_WORSE)
│   │   │   ├── severity_threshold.py  # SeverityThreshold
│   │   │   └── severity_policy.py     # SeverityPolicy (resolves severity from a value)
│   │   ├── discovery.py               # discover_rules() — imports all rule modules
│   │   ├── registry.py                # build_rules() / get_default_rules()
│   │   ├── result.py                  # RuleResult
│   │   ├── financial/
│   │   │   ├── revenue/revenue_growth.py                 # R001
│   │   │   ├── margins/ebitda_margin.py                  # R003
│   │   │   └── profitability/
│   │   │       ├── negative_ebitda.py                    # R002
│   │   │       ├── financial_expenses_to_ebitda.py       # R005
│   │   │       ├── ebitda_inventory_contribution.py      # R006
│   │   │       └── interest_coverage_ratio.py             # R007
│   │   └── sustainability/leverage/nfp_to_ebitda.py       # R004
│   └── services/
│       ├── assessment_service.py            # AssessmentService
│       ├── assessment_status_calculator.py  # AssessmentStatusCalculator
│       └── service_factory.py               # create_default_assessment_service()
├── tests/                              # Mirrors the src/ layout (unit, integration, workflow tests)
│   ├── conftest.py                     # Shared `assessment_service` pytest fixture
│   └── integration/test_credit_assessment.py
├── pyproject.toml                      # pytest configuration (markers, addopts)
└── requirements.txt                    # Runtime and development dependencies
```

## Deterministic rule engine

The deterministic layer is the authoritative core of the system and consists of several cooperating pieces:

- **`Rule` (`src/rules/base/rule.py`)** — abstract base class for every business rule. Concrete rules implement `evaluate(position) -> RuleResult`. `Rule` also provides:
  - a class-level `_registry` and `Rule.register(rule_id)` decorator, used by every concrete rule to register itself under a `rule_id` (e.g. `R001`);
  - `_result(...)` / `_not_evaluable(...)` helpers that build a `RuleResult`, automatically prefixing the `reason` with `[rule_id - rule_name]` for traceability, and resolving severity through the rule's `SeverityPolicy`.
- **`RuleConfig` (`src/rules/base/config.py`)** — an immutable dataclass holding `rule_id`, `rule_name`, `category`, `threshold`, `severity`, `severity_direction`, and `severity_thresholds`. Validates that `rule_id`, `rule_name`, and `category` are non-empty.
- **`RuleStatus` (`src/rules/base/status.py`)** — one of `TRIGGERED`, `NOT_TRIGGERED`, `NOT_EVALUABLE`. `NOT_EVALUABLE` is used whenever the required input data is missing, and it is **never** treated as a triggered rule.
- **`RuleSeverity` (`src/rules/base/severity.py`)** — `LOW`, `MEDIUM`, `HIGH`.
- **`SeverityDirection` / `SeverityThreshold` / `SeverityPolicy`** (`src/rules/base/severity_direction.py`, `severity_threshold.py`, `severity_policy.py`) — allow a rule to escalate severity based on how far a value is from its threshold:
  - `HIGHER_IS_WORSE`: the highest severity threshold that is `<=` the value applies.
  - `LOWER_IS_WORSE`: the highest severity threshold that is `>=` the value applies.
  - If no configured threshold applies, the rule's default `severity` is used.
- **`RuleResult` (`src/rules/result.py`)** — immutable dataclass: `rule_id`, `rule_name`, `category`, `status`, `value`, `threshold`, `severity`, `reason`.
- **`RuleEngine` (`src/engine/rule_engine.py`)** — receives a list of `Rule` instances and, given a `CreditPosition`, calls `rule.evaluate(position)` for each rule, returning one `RuleResult` per configured rule. It contains no business logic of its own.
- **`discover_rules()` (`src/rules/discovery.py`)** — walks the `src.rules` package with `pkgutil.walk_packages` and imports every rule module (skipping `registry`, `discovery`, and anything under `.base.`), which triggers each rule's `@Rule.register(...)` decorator.
- **`build_rules()` / `get_default_rules()` (`src/rules/registry.py`)** — `get_default_rules()` loads `RuleConfig` objects from `config/rules.yaml` via `RuleConfigLoader`, discovers all registered rule classes, and instantiates one `Rule` object per configured `RuleConfig`.
- **`RuleConfigLoader` (`src/config/rule_config_loader.py`)** — parses `config/rules.yaml`, validating that each entry has `rule_id`, `rule_name`, `category`, `threshold`, `severity`, `severity_direction`, and optionally a list of `severity_thresholds` (`threshold` + `severity`). Duplicate `rule_id`s and invalid enum values raise `ValueError`.
- **`RuleConfiguration` (`src/config/rule_configuration.py`)** — `RuleConfiguration.default()` points at `config/rules.yaml`.
- **`AssessmentStatusCalculator` (`src/services/assessment_status_calculator.py`)** — counts `TRIGGERED` results and returns:
  - `NORMAL` when 0 rules are triggered,
  - `ATTENTION` when exactly 1 rule is triggered,
  - `CRITICAL` when 2 or more rules are triggered.
- **`AssessmentService` (`src/services/assessment_service.py`)** — the entry point of the deterministic layer: runs `RuleEngine.evaluate()`, builds `RuleFinding`s for triggered rules that have a configured comment (via `CommentEngine`), computes the `AssessmentStatus`, and returns an `Assessment`.
- **`CommentEngine` / `Comment` (`src/comments/comment_engine.py`, `comment.py`) and `COMMENTS` templates (`src/comments/templates.py`)** — map a `TRIGGERED` `RuleResult` to a human-readable `Comment`, formatted from a per-rule string template (e.g. `"Revenue growth declined to {value:.1%}, ..."`). A missing comment template simply means no `RuleFinding` is produced for that result; it never fails the assessment.

### Implemented rules (from `config/rules.yaml` and `src/rules/`)

| Rule ID | Class | Category | Indicator | Threshold | Direction | Default severity |
|---|---|---|---|---|---|---|
| `R001` | `RevenueGrowthRule` | `revenue` | `revenue_growth` | `-0.10` | `LOWER_IS_WORSE` | `MEDIUM` (escalates to `HIGH` at `-0.30`) |
| `R002` | `NegativeEbitdaRule` | `profitability` | `ebitda` | `0.0` | `LOWER_IS_WORSE` | `HIGH` |
| `R003` | `EbitdaMarginRule` | `profitability` | `ebitda_margin` | `0.0` | `LOWER_IS_WORSE` | `MEDIUM` (escalates to `HIGH` at `-0.10`) |
| `R004` | `NfpToEbitdaRule` | `leverage` | `nfp_to_ebitda` | `5.0` | `HIGHER_IS_WORSE` | `MEDIUM` (escalates to `HIGH` at `7.0`) |
| `R005` | `FinancialExpensesToEbitdaRule` | `profitability` | `interest_expense / ebitda` | `0.60` | `HIGHER_IS_WORSE` | `MEDIUM` (escalates to `HIGH` at `1.00`) |
| `R006` | `EbitdaInventoryContributionRule` | `profitability_quality` | `change_in_finished_goods_inventory / ebitda` | `0.30` | `HIGHER_IS_WORSE` | `MEDIUM` (escalates to `HIGH` at `0.50`) |
| `R007` | `InterestCoverageRatioRule` | `profitability` | `ebitda / interest_expense` | `2.0` | `LOWER_IS_WORSE` | `MEDIUM` (escalates to `HIGH` at `1.0`) |

Each rule explicitly guards against missing or non-meaningful inputs (e.g. `R005`/`R006` return `NOT_EVALUABLE` when `ebitda <= 0`, `R007` returns `NOT_EVALUABLE` when `interest_expense <= 0`) instead of silently producing a misleading numeric result.

`CreditPosition` (`src/models/position.py`) is the structured input consumed by all rules; every financial field defaults to `None`, which each rule interprets as "not evaluable" rather than as a positive or negative signal.

## Analysis Agent

`AnalysisAgent` (`src/agents/analysis/analysis_agent.py`) implements the generic `Agent[Assessment, AssessmentAnalysis]` contract (`src/agents/base/agent.py`) and performs a pure **transformation**, not a second assessment:

- **`key_findings`** — every `RuleFinding` whose underlying `RuleResult.status == TRIGGERED`, converted to an `AnalysisFinding`.
- **`risk_factors`** — the subset of `key_findings` whose `severity == HIGH`.
- **`limitations`** — every `RuleResult` with `status == NOT_EVALUABLE`, converted to an `AnalysisFinding` using the rule's `reason` (or a generic "`<rule_name>` could not be evaluated." message).
- **`assessment_status`** — copied verbatim from `Assessment.status`.

The resulting `AssessmentAnalysis` (`src/models/assessment_analysis.py`) is the controlled boundary handed to the reporting layer: `position_id`, `assessment_status`, `key_findings`, `risk_factors`, `limitations`.

## Reporting Agent

`ReportingAgent` (`src/agents/reporting/reporting_agent.py`) implements `Agent[AssessmentAnalysis, Report]` and coordinates a **primary** `ReportGenerator` with an optional **fallback** `ReportGenerator` (`src/agents/reporting/report_generator.py` defines the `ReportGenerator` abstraction).

Behavior of `ReportingAgent.run(analysis)`:

1. Reset diagnostics (`last_generator_used`, `last_error`) for the current run.
2. Call `report_generator.generate(analysis)`.
   - On success: set `last_generator_used = "PRIMARY"` and return the `Report`.
   - On exception: translate the exception into a concise message via `_get_llm_error_message()` (recognizes rate limiting / `429`, service unavailable / `503`, connection errors, `401`/`403` auth issues, "model not found", timeouts, falling back to a generic message otherwise) and store it in `last_error`.
3. If no `fallback_generator` was configured, the exception is re-raised.
4. Otherwise, `fallback_generator.generate(analysis)` is called, `last_generator_used = "FALLBACK"` is set, and the fallback `Report` is returned. If the fallback also raises, `last_generator_used` is reset to `None` and the exception propagates.

These `last_generator_used` / `last_error` diagnostics are also surfaced by `AssessmentWorkflow` as `report_generator_used` and `report_generation_error` on `AssessmentWorkflowResult` (`src/models/assessment_workflow.py`), together with per-stage timing (`assessment_elapsed_time`, `analysis_elapsed_time`, `reporting_elapsed_time`, `total_elapsed_time`).

## LLM integration

The LLM is isolated behind the `LLMClient` abstract base class (`src/llm/client.py`), which defines a single method: `generate(prompt: str) -> str`.

Three implementations are provided:

| Client | File | Purpose |
|---|---|---|
| `MockLLMClient` | `src/llm/mock_client.py` | Deterministic, no network — returns a configured `response` (default: `"CRITICAL assessment identified."`), can be made to raise a configured `error`, and records `last_prompt` for prompt-construction tests. Used throughout the automated test suite. |
| `GeminiClient` | `src/llm/gemini_client.py` | Wraps the Google `genai` SDK. Reads `GEMINI_API_KEY` from the environment (or an explicit `api_key` argument) and raises `ValueError` if neither is set. Defaults: `model="gemini-3.5-flash"`, `temperature=0.2`, `max_output_tokens=2048`. Raises `ValueError` if Gemini returns an empty response. |
| `OllamaClient` | `src/llm/ollama_client.py` | Wraps the `ollama` Python client for locally hosted models. Requires an explicit `model` name; defaults: `host="http://localhost:11434"`, `temperature=0.0`, `num_predict=512`. Calls `generate(..., stream=False, think=False)`. |

**Prompt construction** (`src/llm/prompt_builder.py`, `src/llm/prompt_template.py`):

- `ReportPromptBuilder.build(analysis)` groups `analysis.key_findings` by `category`, orders findings within each category by severity (`HIGH` → `MEDIUM` → `LOW`), formats them as bullet lines (explicitly **excluding internal rule IDs**), and renders them into the static `ReportPromptTemplate`.
- `ReportPromptTemplate` supplies fixed instruction blocks: `ROLE`, `ARCHITECTURAL_BOUNDARY`, `GROUNDING_RULES`, the deterministic findings themselves, `NARRATIVE_GUIDANCE`, and `OUTPUT_CONTRACT`. Together these explicitly instruct the model to use only supplied information, never reassess the credit position, never state or imply an assessment status or credit decision, never invent figures or causes, and to return prose only (no headings, no bullet points, no rule IDs/thresholds).

**`LLMReportGenerator`** (`src/agents/reporting/llm_report_generator.py`):

1. Builds the prompt from the `AssessmentAnalysis` via `ReportPromptBuilder`.
2. Calls `llm_client.generate(prompt)`.
3. Validates the raw response (`_validate_response`): an empty or whitespace-only response raises `ValueError("LLM returned an empty response")`.
4. Prepends the deterministic `assessment_status` to the LLM narrative itself (`_build_executive_summary`) — the status text in the final summary is added by the application, **not** generated by the model.
5. Builds `findings_by_category` (`ReportFindingGroup` list) directly from `analysis.key_findings` — independent of the LLM output.
6. Returns a `Report` whose `assessment_status`, `findings_by_category`, and `limitations` all come from the deterministic `AssessmentAnalysis`; only `executive_summary` contains generated text.

## Deterministic fallback

`DeterministicReportGenerator` (`src/agents/reporting/deterministic_report_generator.py`) produces a full `Report` without any external dependency:

- Builds a canned `executive_summary` based on `assessment_status` (`NORMAL` / `ATTENTION` / `CRITICAL`, with an `UNDEFINED` message as a defensive default), followed by a bulleted list of `risk_factors` if any exist, otherwise a bulleted list of `key_findings`.
- Groups `key_findings` into `ReportFindingGroup`s by category, exactly like the LLM path.
- Copies `limitations` straight from the `AssessmentAnalysis`.

It is used in two ways:

- as the **sole** report generator when the workflow is built with `use_llm=False` (the default — see `workflow_factory.create_default_assessment_workflow`);
- as the **fallback generator** passed to `ReportingAgent` when `use_llm=True`, so that any LLM failure (network error, auth failure, quota exhaustion, empty/invalid response, etc.) automatically degrades to this deterministic path instead of failing the whole workflow.

## Supported reporting modes

`create_default_assessment_workflow(use_llm: bool = False, llm_client: LLMClient | None = None)` (`src/agents/workflow/workflow_factory.py`) exposes exactly two configurations:

1. **Deterministic-only reporting** (`use_llm=False`, the default) — `ReportingAgent` is configured with `DeterministicReportGenerator` as its only generator; no `llm_client` is required.
2. **LLM-assisted reporting with deterministic fallback** (`use_llm=True`) — requires an `llm_client` (a `GeminiClient`, `OllamaClient`, or `MockLLMClient` instance); `ReportingAgent` is configured with `LLMReportGenerator` as the primary generator and `DeterministicReportGenerator` as the fallback.

In both modes, `AssessmentService`, `AnalysisAgent`, and the resulting `Assessment` / `AssessmentAnalysis` are identical — only the reporting strategy changes.

## Installation

Requirements: Python (the compiled test artifacts in the repository target CPython 3.13).

```bash
# 1. Clone the repository and enter it
git clone <repository-url>
cd credit-assessment-system

# 2. Create and activate a virtual environment
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

`requirements.txt` declares the following dependencies:

```text
google-genai==2.18.0
pytest==9.1.1
pytest-cov==7.1.0
mypy==2.3.0
ruff==0.12.8
streamlit==1.61.1
PyYAML==6.0.2
types-PyYAML
ollama==0.6.2
```

## Environment configuration

The only environment variable read directly by the codebase is:

| Variable | Used by | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | `src/llm/gemini_client.py` (`GeminiClient.__init__`) | Google Gemini API key. If not passed explicitly as the `api_key` constructor argument, `GeminiClient` reads it from `os.getenv("GEMINI_API_KEY")` and raises `ValueError` if it is missing. |

Example (Linux/macOS shell):

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

No `.env` file, `.env.example`, or environment-loading library (e.g. `python-dotenv`) is present in the repository, so the variable must be exported in the shell/session or provided directly via `GeminiClient(api_key=...)`.

For local, offline LLM usage, `OllamaClient` connects to an Ollama server (default `http://localhost:11434`) — no API key is required, but the target `model` and, if not local, `host` must be provided explicitly when constructing the client; there is no dedicated environment variable for these in the current code.

## Running the Streamlit application

`streamlit==1.61.1` is declared as a dependency in `requirements.txt`, but **no Streamlit application file (e.g. an `app.py` or a `pages/` directory) is present in this repository** — no source file under `src/` imports `streamlit`. Streamlit is therefore currently a **declared dependency for a planned/optional UI layer**, not yet an implemented entry point.

To exercise the system today, use the workflow and orchestration API directly, e.g.:

```python
from src.orchestration.orchestrator_factory import create_default_orchestrator
from src.models.position import CreditPosition

orchestrator = create_default_orchestrator()

position = CreditPosition(
    position_id="POS-001",
    revenue_growth=-0.15,
    ebitda=120_000,
    ebitda_margin=0.08,
    nfp_to_ebitda=4.2,
    interest_expense=40_000,
)

report = orchestrator.run(position)

print(report.assessment_status)
print(report.executive_summary)
```

If a Streamlit UI is added on top of `AssessmentOrchestrator` / `AssessmentWorkflow`, it can be run with the standard command once such a script exists:

```bash
streamlit run <path-to-app>.py
```

## Testing

Tests are written with `pytest` and mirror the `src/` package layout under `tests/` (unit tests per rule, per severity component, per service, per agent, per LLM client, plus `tests/integration/test_credit_assessment.py` for end-to-end coverage and a shared `assessment_service` fixture in `tests/conftest.py`).

`pyproject.toml` configures pytest to skip Ollama-dependent tests by default:

```toml
[tool.pytest.ini_options]
markers = [
    "ollama: tests requiring a running Ollama instance",
]
addopts = "-m 'not ollama'"
```

Run the full test suite:

```bash
python -m pytest
```

Run with coverage:

```bash
python -m pytest --cov=src --cov-report=term-missing
```

Run the tests that require a running Ollama instance (excluded by default):

```bash
python -m pytest -m ollama
```

## Ruff / linting

Static analysis is performed with `ruff==0.12.8` (declared in `requirements.txt`; no `ruff.toml` or `[tool.ruff]` section is present in `pyproject.toml`, so default Ruff settings apply):

```bash
python -m ruff check .
```

Type checking can be run with `mypy` (also declared as a dependency, alongside `types-PyYAML`):

```bash
python -m mypy src
```

## Configuration

All deterministic business parameters live in `config/rules.yaml` and are loaded by `RuleConfigLoader` (`src/config/rule_config_loader.py`) into a list of `RuleConfig` objects, then turned into `Rule` instances by `get_default_rules()` (`src/rules/registry.py`).

Each entry under `rules:` requires:

```yaml
rules:
  - rule_id: R00X
    rule_name: <human-readable name>
    category: <category string>
    threshold: <float>
    severity: LOW | MEDIUM | HIGH
    severity_direction: LOWER_IS_WORSE | HIGHER_IS_WORSE
    severity_thresholds:            # optional
      - threshold: <float>
        severity: LOW | MEDIUM | HIGH
      - threshold: <float>
        severity: LOW | MEDIUM | HIGH
```

`RuleConfigLoader` validates required fields, rejects duplicate `rule_id`s, and converts `severity` / `severity_direction` strings into the corresponding `RuleSeverity` / `SeverityDirection` enum members, raising `ValueError` on invalid or missing data.

`RuleConfiguration.default()` (`src/config/rule_configuration.py`) points at `Path("config/rules.yaml")` relative to the working directory; a different `RuleConfiguration` can be passed explicitly to `get_default_rules(configuration=...)` to load rules from another path.

Adding a new rule requires:

1. Implementing a `Rule` subclass under `src/rules/...`, decorated with `@Rule.register("R00X")`.
2. Adding a corresponding entry to `config/rules.yaml`.
3. Optionally adding a comment template for the new `rule_id` in `src/comments/templates.py` so that triggered results produce a human-readable `RuleFinding`.

No changes to `RuleEngine`, `AssessmentService`, `AnalysisAgent`, or the reporting layer are required.

## Example workflow

Using the default, fully-deterministic configuration (`use_llm=False`):

```python
from src.orchestration.orchestrator_factory import create_default_orchestrator
from src.models.position import CreditPosition

orchestrator = create_default_orchestrator()

position = CreditPosition(
    position_id="ACME-2026",
    revenue_growth=-0.35,      # triggers R001 at HIGH severity
    ebitda=-50_000,            # triggers R002
    ebitda_margin=-0.05,       # triggers R003
    nfp_to_ebitda=8.0,         # triggers R004 at HIGH severity
    interest_expense=30_000,
)

report = orchestrator.run(position)

print(report.assessment_status)        # AssessmentStatus.CRITICAL
print(report.executive_summary)        # Deterministic executive summary text
for group in report.findings_by_category:
    print(group.category, [f.text for f in group.findings])
print(report.limitations)              # Findings for any NOT_EVALUABLE rules
```

Enabling LLM-assisted reporting with a deterministic fallback:

```python
from src.agents.workflow.workflow_factory import create_default_assessment_workflow
from src.orchestration.orchestrator import AssessmentOrchestrator
from src.llm.gemini_client import GeminiClient   # requires GEMINI_API_KEY

llm_client = GeminiClient()  # or OllamaClient(model="..."), or MockLLMClient() for tests

workflow = create_default_assessment_workflow(use_llm=True, llm_client=llm_client)
orchestrator = AssessmentOrchestrator(workflow=workflow)

report = orchestrator.run(position)
```

If `llm_client.generate(...)` raises, or returns an empty response, `ReportingAgent` transparently falls back to `DeterministicReportGenerator`; the returned `Report`'s `assessment_status`, `findings_by_category`, and `limitations` are unaffected either way.

## Design principles

Distilled from `docs/architecture.md` and the implementation itself:

- **Deterministic assessment authority** — `Assessment.status` is computed exclusively by `AssessmentStatusCalculator` from deterministic `RuleResult`s.
- **Complete rule evaluation** — the engine always produces exactly one `RuleResult` per configured rule (`len(assessment.rule_results) == len(rule_engine.rules)`).
- **`NOT_EVALUABLE` ≠ `TRIGGERED`** — missing data never contributes to a worse assessment status.
- **Status/finding/limitation preservation** — `Assessment.status == AssessmentAnalysis.assessment_status == Report.assessment_status`; deterministic findings and limitations are propagated, never regenerated, by the analysis and reporting layers.
- **LLM isolation** — the LLM can only produce the `executive_summary` narrative; it cannot alter `RuleResult`s, `AssessmentStatus`, severities, thresholds, findings, or limitations.
- **Reporting resilience** — an LLM failure (`ReportingAgent`'s primary generator raising) triggers the deterministic fallback rather than failing the assessment.
- **Provider independence** — `LLMReportGenerator` depends on the `LLMClient` interface, so `GeminiClient`, `OllamaClient`, and `MockLLMClient` are interchangeable without touching the reporting or assessment layers.
- **Dependency injection and factories** — `AssessmentService`, `AssessmentWorkflow`, and `ReportingAgent` all receive their dependencies through their constructors; `service_factory.py`, `workflow_factory.py`, and `orchestrator_factory.py` centralize the default wiring, keeping unit tests free to inject mocks.

## Limitations

Based on what is (and is not) present in the repository:

- **No Streamlit UI is implemented**, despite `streamlit` being a declared dependency — there is currently no way to run the system as a web app out of the box.
- **No environment file (`.env`) or configuration-loading mechanism** is present for `GEMINI_API_KEY`; it must be set manually in the shell or process environment.
- **No CI workflow files** (e.g. `.github/workflows/*.yml`) are present in the repository, although `docs/architecture.md` describes an intended GitHub Actions pipeline running Ruff and pytest.
- **LLM response validation is intentionally lightweight**: `LLMReportGenerator._validate_response` only rejects empty/whitespace responses. There is no automated check that the generated narrative is semantically consistent with the deterministic findings (a stronger validator, e.g. checking that the deterministic status text is present, is discussed as a future direction in `docs/validation.md` but is not implemented in `src/`).
- **`AssessmentStatusCalculator` uses a simple triggered-rule count** (`0 → NORMAL`, `1 → ATTENTION`, `>=2 → CRITICAL`) rather than a severity-weighted or category-weighted aggregation.
- **Only seven rules are currently configured** (`R001`–`R007`, covering revenue growth, EBITDA, EBITDA margin, leverage, interest expenses, inventory-driven EBITDA quality, and interest coverage); comment templates exist for all except no additional categories (e.g. liquidity, collateral) are covered yet.
- **No REST/HTTP API layer** exists; the system is currently consumed as a Python library through `AssessmentOrchestrator` / `AssessmentWorkflow`.
- **Real Gemini/Ollama calls are excluded from the default automated test run** (`addopts = "-m 'not ollama'"` in `pyproject.toml`, and `MockLLMClient` used throughout `tests/`), so external LLM behavior is not exercised by `python -m pytest` alone.

## Future improvements

Directions explicitly discussed in `docs/architecture.md` (§51) and `docs/validation.md` (§35–36), consistent with the current codebase's extension points:

- **Additional rules** — new financial/business rules can be added by implementing a `Rule` subclass and a `config/rules.yaml` entry, without changes to the analysis or reporting layers.
- **Additional LLM providers** — new `LLMClient` implementations (e.g. an `OpenAIClient` or a different local-LLM client) can be plugged in alongside `GeminiClient`, `OllamaClient`, and `MockLLMClient`.
- **Structured LLM output** — evolving the LLM path from free-form narrative to schema-constrained output that can be automatically cross-checked against `AssessmentAnalysis`.
- **Stronger semantic validation** — a dedicated semantic validator between `LLMReportGenerator` and the final `Report`, checking for unsupported claims, contradictions, missing findings, or numerical inconsistencies, beyond the current empty-response check.
- **Application interfaces** — exposing `AssessmentOrchestrator` / `AssessmentWorkflow` through a REST API and/or the currently-undeveloped Streamlit UI implied by the `streamlit` dependency.
- **Continuous Integration** — adding the GitHub Actions pipeline (Ruff + pytest) described in the architecture documentation but not yet present in the repository.
- **Larger-scale and human-in-the-loop LLM evaluation** — systematic hallucination-rate benchmarking, human review of generated executive summaries, and latency/cost tracking for the LLM reporting path.

---

*This README was generated strictly from the contents of the uploaded repository (`src/`, `config/`, `tests/`, `docs/`, `requirements.txt`, `pyproject.toml`). No feature, command, or file not present in the repository has been invented.*