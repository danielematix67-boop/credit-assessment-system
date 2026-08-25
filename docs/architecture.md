# Architecture

## 1. Overview

This project is a **Credit Assessment System**: a rule-based (deterministic) engine that evaluates a company's financial position, produces a set of triggered/not-triggered findings, computes an overall risk status, and generates a human-readable report — optionally enriched by an LLM for narrative generation.

The system is designed around one central principle:

> **The deterministic rule engine is the sole source of truth for the assessment. Any LLM involved in the pipeline is used exclusively for language generation (the executive narrative) and can never alter, override, or reinterpret the outcome of the assessment.**

This principle ("architectural boundary") is enforced structurally (interfaces, data flow, prompt design) rather than only by convention, and is explicitly documented and reiterated inside the LLM prompt itself (see [§6.3](#63-prompting-strategy-and-the-architectural-boundary)).

The system is delivered as:
- A **Python library** (`src/`) implementing the assessment domain logic, fully decoupled from any UI or delivery mechanism.
- A **Streamlit web application** (`app/`) that acts as a thin presentation layer on top of the library.
- A comprehensive **automated test suite** (`tests/`) mirroring the source tree, with unit and integration coverage.

---

## 2. Goals and Design Principles

| Principle | Description |
|---|---|
| **Determinism first** | Credit-risk assessment is a regulated, auditable domain. The outcome (status, findings, severities) is always produced by explicit, versionable, YAML-configured business rules — never by a model. |
| **Separation of concerns** | Each layer has a single responsibility: rules only evaluate; the comment engine only translates results into text; the reporting agent only assembles reports; the LLM only writes prose. |
| **Pluggable rules** | New business rules can be added by dropping a new class into `src/rules/**`, self-registering via a decorator, and adding a corresponding YAML entry — no changes to the engine are required (Open/Closed Principle). |
| **Pluggable LLM backends** | The system can run with no LLM (`Deterministic` mode), a hosted LLM (Google Gemini), or a local LLM (Ollama) — all behind the same `LLMClient` abstraction. |
| **Graceful degradation** | If the LLM is unavailable, times out, or returns an invalid/empty response, the system automatically falls back to the deterministic report generator. The credit assessment result itself is never affected — only the wording of the executive summary changes. |
| **Testability** | Every layer is built around small, dependency-injected classes with abstract interfaces (`Agent`, `Rule`, `ReportGenerator`, `LLMClient`), so each layer can be unit-tested and mocked in isolation (see `MockLLMClient`). |
| **UI/Domain decoupling** | The Streamlit application never contains business logic. It only builds input objects, invokes the workflow, and renders the resulting immutable data structures. |

---

## 3. High-Level Architecture

The system is organized as a **layered / clean architecture**, with a clear one-directional dependency flow: the presentation layer (`app/`) depends on the domain layer (`src/`); the domain layer never depends on the presentation layer.

At the domain level, the assessment is executed as a three-stage **pipeline** (implemented as an internal multi-agent workflow), orchestrated by a thin orchestration layer:

```
CreditPosition
      │
      ▼
┌─────────────────────┐
│ 1. Assessment Service │  Deterministic rule evaluation + comment generation + status calculation
└─────────────────────┘
      │  Assessment
      ▼
┌─────────────────────┐
│ 2. Analysis Agent     │  Structures the assessment into key findings / risk factors / limitations
└─────────────────────┘
      │  AssessmentAnalysis
      ▼
┌─────────────────────┐
│ 3. Reporting Agent    │  Produces the final Report (deterministic text or LLM-assisted narrative)
└─────────────────────┘
      │  Report
      ▼
  Presentation (Streamlit UI)
```

This pipeline is encapsulated by `AssessmentWorkflow` (`src/agents/workflow/assessment_workflow.py`), which also captures timing metrics and reporting provenance (which generator was actually used, and why), and is exposed to callers through `AssessmentOrchestrator` (`src/orchestration/orchestrator.py`) for simplified, report-only consumption.

### 3.1 Component Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                              app/ (Streamlit UI)                          │
│                                                                             │
│  streamlit_app.py  ──▶  app/ui/*  (sidebar, input source, results, ...)   │
│         │                                                                   │
│         ▼                                                                   │
│  app/workflow/assessment_workflow_factory.py  ──▶  builds AssessmentWorkflow│
│  app/workflow/runner.py                        ──▶  executes the workflow  │
│  app/config.py                                 ──▶  secrets / env config   │
└───────────────────────────────────────────────────────────────────────────┘
                                    │ depends on
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                              src/ (Domain library)                        │
│                                                                             │
│  orchestration/   AssessmentOrchestrator, orchestrator_factory            │
│  agents/          workflow/, analysis/, reporting/, base/ (Agent ABC)     │
│  services/        AssessmentService, AssessmentStatusCalculator, factory  │
│  engine/          RuleEngine, FindingEngine                               │
│  rules/           base/, discovery.py, registry.py, financial/, ...      │
│  comments/        CommentEngine, Comment, templates                      │
│  config/          RuleConfigLoader, RuleConfiguration                    │
│  llm/             LLMClient (ABC), GeminiClient, OllamaClient, MockLLMClient, │
│                    ReportPromptBuilder, ReportPromptTemplate              │
│  models/          Immutable dataclasses: CreditPosition, Assessment,      │
│                    AssessmentAnalysis, Report, AssessmentWorkflowResult   │
└───────────────────────────────────────────────────────────────────────────┘
                                    │ configured by
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                       config/rules.yaml (externalized rule config)        │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Repository Structure

```
progetto/
├── app/                            # Streamlit presentation layer
│   ├── streamlit_app.py            # Application entry point
│   ├── config.py                   # Secrets / environment resolution
│   ├── demo_scenarios.py           # Pre-built demo credit positions
│   ├── ui/                         # UI components (sidebar, forms, results, styling)
│   └── workflow/
│       ├── assessment_workflow_factory.py   # Builds an AssessmentWorkflow per reporting mode
│       └── runner.py                        # Thin execution wrapper
│
├── src/                             # Domain library (framework-agnostic)
│   ├── models/                      # Immutable data contracts (dataclasses)
│   ├── rules/                       # Rule catalog, base classes, discovery & registry
│   │   ├── base/                    # Rule ABC, severity model, config, status
│   │   ├── financial/                # revenue/, margins/, profitability/
│   │   └── sustainability/           # leverage/
│   ├── engine/                      # RuleEngine, FindingEngine
│   ├── comments/                    # CommentEngine + templates
│   ├── services/                    # AssessmentService, status calculator, factory
│   ├── agents/                      # Analysis agent, Reporting agent, Workflow, base Agent ABC
│   ├── orchestration/               # Orchestrator + factory
│   ├── llm/                         # LLM client abstraction + implementations + prompt building
│   └── config/                      # Rule configuration loading (YAML → RuleConfig)
│
├── config/
│   └── rules.yaml                   # Declarative rule catalog (thresholds, severities)
│
├── tests/                           # Mirrors src/ and app/ 1:1, unit + integration
│   └── integration/
│       └── test_credit_assessment.py
│
└── requirements.txt
```

---

## 5. Domain Model

All domain objects are **immutable dataclasses** (`@dataclass(frozen=True)`), except `CreditPosition`, which is a mutable input container. Immutability guarantees that once an assessment stage produces a result, no downstream stage (including the LLM-backed reporting stage) can silently mutate it.

| Model | Purpose |
|---|---|
| `CreditPosition` | The input: raw and derived financial figures for one company/position (revenue, EBITDA, leverage, growth, etc.). All fields are `float \| None`, so partial/missing data is explicit and rules must handle it. |
| `RuleResult` | The atomic output of a single rule: id, name, category, `RuleStatus`, numeric value, threshold, resolved `RuleSeverity`, and a human-readable reason. |
| `Comment` | A rule-specific, templated natural-language explanation, generated only for `TRIGGERED` results. |
| `RuleFinding` | Pairs a `RuleResult` with its `Comment`. |
| `Assessment` | The full deterministic output: all `RuleResult`s, all `RuleFinding`s, and the aggregated `AssessmentStatus`. |
| `AnalysisFinding` | A normalized (rule_id, category, severity, text) unit used downstream by both reporting paths. |
| `AssessmentAnalysis` | Structured triage of the assessment: `key_findings` (all triggered), `risk_factors` (HIGH-severity triggered), `limitations` (rules that could not be evaluated). |
| `Report` | The final deliverable: executive summary, findings grouped by category, and limitations. |
| `AssessmentWorkflowResult` | Wraps `Assessment`, `AssessmentAnalysis`, `Report`, plus **provenance** (`report_generator_used`: `PRIMARY`/`FALLBACK`, `report_generation_error`) and **timing metrics** for each pipeline stage. |

### 5.1 Status & Severity Enumerations

- `RuleStatus`: `TRIGGERED`, `NOT_TRIGGERED`, `NOT_EVALUABLE`.
- `RuleSeverity`: `LOW`, `MEDIUM`, `HIGH`.
- `SeverityDirection`: `HIGHER_IS_WORSE`, `LOWER_IS_WORSE` — defines how a rule's numeric value maps to severity thresholds.
- `AssessmentStatus`: `NORMAL`, `ATTENTION`, `CRITICAL`.

---

## 6. Core Layers

### 6.1 Rules Layer (`src/rules/`)

This is the heart of the deterministic engine.

**Rule base class (`src/rules/base/rule.py`)**
- Abstract `Rule(ABC)` with a single abstract method, `evaluate(position) -> RuleResult`.
- Provides shared helpers to all concrete rules: `_result()`, `_not_evaluable()`, `_severity()`, `_format_reason()` — ensuring every `RuleResult` is built consistently and every reason string is automatically tagged with `[rule_id - rule_name]` for traceability.
- Implements a **self-registration mechanism** via the class-method decorator `Rule.register(rule_id)`, backed by a class-level registry dict (`Rule._registry`). Registering the same `rule_id` twice raises an error, guaranteeing uniqueness.

**Severity resolution (`SeverityPolicy`, `SeverityThreshold`, `SeverityDirection`)**
- Each rule can define graduated severity thresholds (e.g., MEDIUM at –10% revenue growth, HIGH at –30%).
- `SeverityPolicy.evaluate(value)` picks the *worst applicable* threshold given the configured direction, falling back to the rule's default severity when no threshold applies.

**Rule discovery & registry (`discovery.py`, `registry.py`)**
- `discover_rules()` walks the `src.rules` package with `pkgutil.walk_packages` and imports every module (excluding `registry`, `discovery`, and `base/*`), causing every `@Rule.register(...)`-decorated class to self-register as a side effect of import. This is intentionally idempotent — re-importing does not re-execute registration.
- `build_rules(configs)` / `get_default_rules(configuration)` load the YAML rule configuration (`config/rules.yaml`) via `RuleConfigLoader`, then instantiate one concrete `Rule` subclass per configured `rule_id` by resolving it from the registry.

**Concrete rule catalog**

| Rule ID | Category | Direction | Description |
|---|---|---|---|
| R001 | `revenue` | Lower is worse | Revenue growth deterioration |
| R002 | `profitability` | Lower is worse | Negative EBITDA |
| R003 | `profitability` | Lower is worse | EBITDA margin deterioration |
| R004 | `leverage` | Higher is worse | NFP / EBITDA leverage |
| R005 | `profitability` | Higher is worse | Interest expense to EBITDA |
| R006 | `profitability_quality` | Higher is worse | EBITDA materially supported by finished-goods inventory increase |
| R007 | `profitability` | Lower is worse | Interest coverage ratio |

Each rule lives under a subpackage reflecting its business category (e.g. `src/rules/financial/revenue/`, `src/rules/financial/profitability/`, `src/rules/sustainability/leverage/`), and follows the same pattern: read one field from `CreditPosition`, return `_not_evaluable(...)` if it is `None`, otherwise compare against `self.config.threshold` and return `_result(...)`.

Adding a new rule requires only:
1. A new class extending `Rule`, decorated with `@Rule.register("R00X")`.
2. A corresponding entry in `config/rules.yaml`.

No change to `RuleEngine`, `discovery.py`, or `registry.py` is needed — this is the system's main extensibility point.

### 6.2 Rule Configuration (`config/rules.yaml` + `src/config/`)

Rules are **externalized as data**, not hardcoded, so risk thresholds can be tuned without touching code (and, in principle, differ per environment/portfolio).

- `RuleConfigLoader.load(path)` parses and strictly validates the YAML: required fields per rule (`rule_id`, `rule_name`, `category`, `threshold`, `severity`, `severity_direction`), duplicate `rule_id` detection, and per-item validation of optional `severity_thresholds`.
- `RuleConfiguration.default()` resolves the default path (`config/rules.yaml`), keeping the loader itself path-agnostic and testable.

### 6.3 Execution Engine (`src/engine/`)

- **`RuleEngine.evaluate(position)`** — executes every configured `Rule` against a `CreditPosition` and returns the ordered list of `RuleResult`s. It contains **no business logic** of its own; it only orchestrates the "map" over rules, by design (see its own docstring).
- **`FindingEngine.generate(result)`** — a currently-unused-by-the-primary-path (but tested) alternative entry point that turns one `RuleResult` into an optional `RuleFinding` via the `CommentEngine`, mirroring the logic embedded in `AssessmentService`.

### 6.4 Comment Engine (`src/comments/`)

- `CommentEngine.generate(result)` converts a `TRIGGERED` `RuleResult` into a human-readable `Comment`, using a lookup table of Python format strings keyed by `rule_id` (`src/comments/templates.py`). Non-triggered or unmapped results yield `None`.
- This keeps **presentation text** for triggered rules fully decoupled from the **evaluation logic** that decided they triggered.

### 6.5 Assessment Service (`src/services/`)

`AssessmentService.assess(position)` is the entry point for stage 1 of the pipeline:
1. Runs `RuleEngine.evaluate(position)` → all `RuleResult`s.
2. For each result, asks `CommentEngine.generate(result)` for a comment; results with a comment become `RuleFinding`s.
3. Delegates the overall `AssessmentStatus` to `AssessmentStatusCalculator`.
4. Returns an immutable `Assessment`.

`AssessmentStatusCalculator` implements the current business policy for aggregate risk status:
- `≥ 2` triggered rules → `CRITICAL`
- `1` triggered rule → `ATTENTION`
- `0` triggered rules → `NORMAL`

`service_factory.create_default_assessment_service()` wires together `RuleEngine` (with rules loaded from the default YAML config), `CommentEngine`, and `AssessmentStatusCalculator` — the standard composition root for stage 1.

### 6.6 Agents Layer (`src/agents/`)

The system uses a lightweight, generic **Agent** abstraction (`Agent[InputT, OutputT]`, `src/agents/base/agent.py`) — a `Generic`, `ABC` base class exposing a single `run(input_data) -> output` method. Both `AnalysisAgent` and `ReportingAgent` implement it, allowing the workflow to treat them uniformly and be tested via simple stand-ins.

#### Analysis Agent (`src/agents/analysis/analysis_agent.py`)
`AnalysisAgent(Agent[Assessment, AssessmentAnalysis])` — a purely deterministic transformation:
- `key_findings`: all findings whose underlying result is `TRIGGERED`.
- `risk_factors`: the subset of `key_findings` with `HIGH` severity.
- `limitations`: rules whose status was `NOT_EVALUABLE`, surfaced as findings so missing/insufficient input data is never silently hidden from the final report.

#### Reporting Agent (`src/agents/reporting/reporting_agent.py`)
`ReportingAgent(Agent[AssessmentAnalysis, Report])` implements the **Strategy pattern with automatic fallback**:
- Wraps a *primary* `ReportGenerator` (deterministic or LLM-backed) and an *optional fallback* `ReportGenerator` (always deterministic, in practice).
- On success, records provenance (`last_generator_used = "PRIMARY"`).
- On any exception from the primary generator, it:
  1. Normalizes the exception into a concise, human-readable message via `_get_llm_error_message()` (covers rate limiting, service unavailability, connection failures, auth/permission errors, missing models, and timeouts, with a generic fallback message otherwise).
  2. Logs a warning and records `last_error`.
  3. If a fallback generator is configured, invokes it and records `last_generator_used = "FALLBACK"`. If the fallback itself fails, the exception propagates and `last_generator_used` is reset to `None`.
  4. If no fallback is configured, re-raises the original exception.

This gives the system **resilience against LLM outages** without ever affecting the correctness of the underlying deterministic assessment — only the executive narrative's prose changes.

`ReportGenerator` (`src/agents/reporting/report_generator.py`) is the abstract strategy interface (`generate(analysis) -> Report`), with two implementations:

- **`DeterministicReportGenerator`** — builds the executive summary via simple, status-dependent template text plus a bullet list of risk factors (or key findings if no HIGH-severity items exist), and groups findings by category. Fully offline, zero external dependencies, always available.
- **`LLMReportGenerator`** — delegates only the narrative paragraph to an `LLMClient`; the assessment status, findings, categories, and limitations are still taken verbatim from the deterministic `AssessmentAnalysis`. It validates the LLM response is non-empty (`_validate_response`) and prepends the deterministic status line to the LLM narrative (`_build_executive_summary`) so that the status is **never LLM-generated**.

#### Workflow (`src/agents/workflow/assessment_workflow.py`)
`AssessmentWorkflow` is the concrete pipeline runner, composing `AssessmentService → AnalysisAgent → ReportingAgent` and measuring elapsed time for each stage plus the total, in addition to surfacing the reporting agent's provenance fields (`report_generator_used`, `report_generation_error`) onto the final `AssessmentWorkflowResult`.

`workflow_factory.create_default_assessment_workflow(use_llm, llm_client)` is a convenience composition root for library consumers (e.g., scripts, tests, notebooks) that need a ready-to-run workflow without going through the Streamlit-specific factory.

### 6.7 Orchestration Layer (`src/orchestration/`)

`AssessmentOrchestrator.run(position) -> Report` is a minimal facade over `AssessmentWorkflow.run(position)` for callers that only need the final `Report` and don't care about intermediate artifacts or timing/provenance metadata. `orchestrator_factory.create_default_orchestrator()` wires it to the default (non-LLM) workflow.

### 6.8 LLM Integration (`src/llm/`)

**Client abstraction**
`LLMClient(ABC)` defines a single method, `generate(prompt: str) -> str`, which every concrete client implements:

| Client | Backend | Notes |
|---|---|---|
| `GeminiClient` | Google Gemini (`google-genai` SDK) | Reads `GEMINI_API_KEY` from env or constructor; configurable model/temperature/max tokens. |
| `OllamaClient` | Local Ollama server | Configurable host/model/temperature/`num_predict`; runs with `think=False` for deterministic, fast generation. |
| `MockLLMClient` | In-memory test double | Returns a configurable canned response or raises a configurable exception — used extensively by the test suite to validate the reporting agent's fallback behavior without network calls. |

This abstraction lets the reporting layer, the workflow factory, and the Streamlit UI remain **fully agnostic to the specific LLM provider**; adding a new backend (e.g., OpenAI, Anthropic) only requires a new `LLMClient` subclass.

#### 6.8.1 Prompting Strategy and the Architectural Boundary

`ReportPromptTemplate` (`src/llm/prompt_template.py`) hardcodes, as static instructions embedded in every prompt:
- **Role**: the LLM is a *reporting assistant*, not a credit analyst — it must not reassess the position.
- **Architectural boundary**: explicit instructions not to override, reinterpret, or alter severities/categories/status, and not to imply a credit decision.
- **Grounding rules**: use only the supplied findings; no invented facts, figures, or causal claims; preserve numeric values exactly; never mention internal rule IDs or thresholds.
- **Narrative guidance**: synthesize findings by theme, prioritize HIGH-severity items, avoid repetition, remain professional and concise.
- **Output contract**: return only prose (no headings/bullets), never restate the assessment status (the application adds it deterministically), never mention the LLM itself.

`ReportPromptBuilder` (`src/llm/prompt_builder.py`) prepares the *data* half of the prompt: it groups `AnalysisFinding`s by category, sorts each group by severity (`HIGH` → `MEDIUM` → `LOW`), and renders them into a plain-text block — deliberately excluding rule IDs, since they are considered internal implementation details irrelevant to the narrative.

This design ensures the LLM operates as a **constrained text-rendering function** over a deterministic input, not as a decision-maker — the same guarantee that is also enforced structurally by `LLMReportGenerator` always taking `assessment_status`, `findings_by_category`, and `limitations` directly from the deterministic `AssessmentAnalysis`.

---

## 7. Application Layer (`app/`)

The Streamlit application is a **presentation-only** consumer of the domain library — it never implements assessment logic, only:

1. **Input acquisition** — `app/ui/input_source.py` and `app/ui/credit_position.py` let the user either fill in a manual financial position or select from pre-built `app/demo_scenarios.py` examples.
2. **Configuration** — `app/ui/sidebar.py` and `app/ui/assessment_configuration.py` let the user pick a **reporting mode**:
   - `Deterministic`
   - `Gemini + Fallback`
   - `Ollama + Fallback` (only offered when *not* running on Streamlit Community Cloud, since it requires reaching a local/self-hosted Ollama instance — see `app/config.get_reporting_modes()`).
3. **Workflow construction** — `app/workflow/assessment_workflow_factory.create_workflow(reporting_mode, ...)` builds the concrete `AssessmentWorkflow` for the chosen mode, resolving Gemini/Ollama credentials via `app/config.py` (priority: Streamlit secrets → environment variables → local defaults).
4. **Execution** — `app/workflow/runner.run_assessment(workflow, position)` is a one-line pass-through to `workflow.run(position)`, kept as a separate module purely to make the UI layer's dependency on the domain explicit and mockable in tests.
5. **Result rendering** — `app/ui/results.py` (the largest UI module) renders the `AssessmentWorkflowResult`: status, executive summary, findings grouped by category, limitations, and reporting provenance/timing. `app/ui/workflow_view.py` visualizes the three-stage pipeline itself for transparency. `app/ui/styles.py` centralizes CSS/theming; `app/ui/responsive_table.py` and `app/ui/components.py` provide shared rendering primitives.

Session state (`st.session_state`) is used only to persist the last computed result/position/mode across Streamlit's rerun cycle — no business state lives there.

### 7.1 Secrets & Environment Configuration (`app/config.py`)

- `is_streamlit_cloud()` detects the Streamlit Community Cloud runtime via `STREAMLIT_RUNTIME_ENV` / `STREAMLIT_SHARING_MODE` and is used to hide the `Ollama + Fallback` option in that environment (no local network access to a self-hosted Ollama instance).
- `get_gemini_api_key()` and `get_ollama_configuration()` both resolve configuration with a consistent priority order: **Streamlit secrets → environment variables → sane local defaults**, with defensive `try/except` around `st.secrets` access since it can raise when no secrets file is present (e.g., in CI or local dev without `.streamlit/secrets.toml`).

---

## 8. End-to-End Request Flow

```
User (Streamlit UI)
   │  fills form / picks demo scenario, selects reporting mode, clicks "Run"
   ▼
build_credit_position()            → CreditPosition
   ▼
create_workflow(reporting_mode)    → AssessmentWorkflow (wired for Deterministic / Gemini / Ollama)
   ▼
run_assessment(workflow, position) → AssessmentWorkflow.run(position)
   │
   ├─ 1. AssessmentService.assess(position)
   │       RuleEngine.evaluate(position)      → list[RuleResult]
   │       CommentEngine.generate(result)     → Comment | None  (per triggered rule)
   │       AssessmentStatusCalculator.calc()  → AssessmentStatus
   │       ⇒ Assessment(status, rule_results, findings)
   │
   ├─ 2. AnalysisAgent.run(assessment)
   │       ⇒ AssessmentAnalysis(key_findings, risk_factors, limitations)
   │
   └─ 3. ReportingAgent.run(analysis)
           try: primary ReportGenerator.generate(analysis)
             - Deterministic: template-based executive summary
             - LLM-backed: ReportPromptBuilder + ReportPromptTemplate → LLMClient.generate() → Report
           except: log + fallback DeterministicReportGenerator.generate(analysis)
           ⇒ Report
   ▼
AssessmentWorkflowResult(assessment, analysis, report, provenance, timings)
   ▼
store_assessment_result() → st.session_state
   ▼
render_results() → rendered in the Streamlit UI
```

---

## 9. Cross-Cutting Concerns

### 9.1 Immutability & Data Integrity
All intermediate and final domain objects (`RuleResult`, `Comment`, `RuleFinding`, `Assessment`, `AnalysisFinding`, `AssessmentAnalysis`, `Report`, `AssessmentWorkflowResult`) are frozen dataclasses. This prevents any layer — including UI code or an LLM-adjacent component — from mutating an already-computed assessment result, which is essential for auditability in a credit-risk context.

### 9.2 Missing Data Handling
`CreditPosition` fields are all `float | None`. Every rule explicitly checks for `None` and returns a `NOT_EVALUABLE` result with a clear reason rather than raising an exception or silently skipping the rule. These `NOT_EVALUABLE` results are then surfaced end-to-end as `limitations` in both `AssessmentAnalysis` and the final `Report`, so incomplete input data is always visible to the end user, not hidden by the aggregate status.

### 9.3 Error Handling & Resilience
- **Rule configuration errors** (malformed YAML, missing fields, duplicate IDs, invalid enum values) fail fast at startup with descriptive `ValueError`s from `RuleConfigLoader`.
- **LLM failures** are caught, classified into a human-readable message (`_get_llm_error_message`), logged, and handled via automatic fallback to the deterministic report generator — the assessment result is never lost, only the report's prose quality/style may degrade to the deterministic template.
- **UI-level errors** (invalid manual input, workflow construction failures, execution failures) are caught in `app/ui/assessment.py` and surfaced via `st.error()` / `st.exception()`, with `st.stop()` halting further rendering for that run.

### 9.4 Observability
`AssessmentWorkflowResult` carries per-stage timings (`assessment_elapsed_time`, `analysis_elapsed_time`, `reporting_elapsed_time`, `total_elapsed_time`) plus reporting provenance (`report_generator_used`, `report_generation_error`), all measured with `time.perf_counter()` inside `AssessmentWorkflow.run()`. This is surfaced in the UI (`app/ui/workflow_view.py`, `app/ui/results.py`) to make the pipeline's behavior — including LLM fallbacks — transparent to the end user, and is also asserted on directly in the test suite.

### 9.5 Extensibility Points

| To add... | Do this |
|---|---|
| A new business rule | Create a `Rule` subclass under `src/rules/<domain>/<subdomain>/`, decorate with `@Rule.register("R00X")`, add a matching entry to `config/rules.yaml`. |
| A new LLM backend | Implement `LLMClient.generate(prompt) -> str`; wire it into `app/workflow/assessment_workflow_factory.py` (and, if applicable, `app/config.py` for credential resolution). |
| A new reporting style | Implement `ReportGenerator.generate(analysis) -> Report`; use it as `report_generator` and/or `fallback_generator` in `ReportingAgent`. |
| A new aggregate status policy | Adjust `AssessmentStatusCalculator.calculate()` (currently a simple triggered-rule count threshold: ≥2 → CRITICAL, 1 → ATTENTION, 0 → NORMAL). |
| A new consumer (CLI, API, batch job) | Reuse `src/` directly via `create_default_assessment_workflow()` / `create_default_orchestrator()` — no Streamlit dependency is required. |

---

## 10. Configuration & Secrets Summary

| Setting | Source (priority order) | Used by |
|---|---|---|
| `config/rules.yaml` path | `RuleConfiguration.default()` (`config/rules.yaml`) | `get_default_rules()` |
| `GEMINI_API_KEY` | Streamlit secrets → env var | `GeminiClient`, `app/config.get_gemini_api_key()` |
| Ollama host/model | Streamlit secrets `[ollama]` → env vars (`OLLAMA_HOST`, `OLLAMA_MODEL`) → defaults (`http://localhost:11434`, `qwen3:0.6b`) | `OllamaClient`, `app/config.get_ollama_configuration()` |
| Runtime environment detection | `STREAMLIT_RUNTIME_ENV`, `STREAMLIT_SHARING_MODE` env vars | `app/config.is_streamlit_cloud()` (hides `Ollama + Fallback` on Streamlit Cloud) |

---

## 11. Technology Stack

| Concern | Technology |
|---|---|
| Language | Python 3.13 |
| Web UI | [Streamlit](https://streamlit.io/) `1.61.1` |
| Configuration format | YAML (`PyYAML` `6.0.2`) |
| Hosted LLM | Google Gemini via `google-genai` `2.18.0` |
| Local LLM | [Ollama](https://ollama.com/) via `ollama` `0.6.2` Python client |
| Testing | `pytest` `9.1.1`, `pytest-cov` `7.1.0` |
| Static analysis | `mypy` `2.3.0` (typed codebase, `X | None` unions throughout), `ruff` `0.12.8` (linting) |

---

## 12. Testing Strategy

The `tests/` tree mirrors `src/` and `app/` 1:1 (43 test modules at the time of writing), including:

- **Unit tests** per layer: rules (`tests/rules/**`, including registry/discovery/severity-configuration behavior), engine (`tests/engine/`), comments (`tests/comments/`), config loading (`tests/config/`), services (`tests/services/`), agents (`tests/agents/**`), LLM clients (`tests/llm/**`, using `MockLLMClient` to simulate both success and failure paths without network access), and orchestration (`tests/orchestration/`).
- **Integration tests** (`tests/integration/test_credit_assessment.py`) exercising the full pipeline end-to-end against representative `CreditPosition` inputs.
- Shared fixtures live in `tests/conftest.py`.

This structure allows any layer to be modified or replaced (e.g., swapping the status-aggregation policy, or adding a new LLM backend) with confidence that regressions are caught close to the change.

---

## 13. Summary

The Credit Assessment System is built as a **deterministic-first, LLM-augmented** pipeline with strict separation between the domain library (`src/`) and its Streamlit presentation layer (`app/`). Business rules are declarative, self-registering, and independently testable; the assessment status and findings are always computed deterministically; and any LLM involvement is confined — by interface design, prompt engineering, and automatic fallback — to producing an executive narrative that can never alter the underlying credit decision.