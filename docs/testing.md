# Test Suite and Quality Gates

This document describes the current test layout under `tests/`, the behaviour protected by each group and the repository's automated quality gates. The test tree and CI workflow are authoritative; this document intentionally avoids maintaining a fixed test count or coverage percentage.

## Testing objectives

The suite protects more than individual rule calculations. It checks that:

1. domain models and input validation preserve their contracts;
2. configured rules resolve to deterministic implementations and return the expected evidence;
3. services aggregate rule results and determine section/case/final status consistently;
4. analysis and reporting preserve the deterministic evidence boundary;
5. provider errors and invalid generated output are handled through the configured fallback;
6. the end-to-end workflow returns a coherent result and execution metadata;
7. application presentation helpers display existing evidence without implementing a second decision engine.

## Test layout

The directory structure broadly mirrors the production packages:

| Test package | Main scope |
|---|---|
| `tests/agents/analysis/` | Case-analysis agent and structured analysis output |
| `tests/agents/reporting/` | Deterministic and LLM report generators, reporting-agent behaviour |
| `tests/agents/workflow/` | Workflow sequencing, factory behaviour and execution metadata |
| `tests/app/demo/` | Synthetic in-code demo-scenario construction |
| `tests/app/ui/` | Focused UI data-frame/presentation helpers, including financial analysis and risk drivers |
| `tests/comments/` | Comment models and deterministic comment engine |
| `tests/config/` | Final-assessment policy and rule configuration loading/validation |
| `tests/engine/` | Rule engine and finding engine |
| `tests/integration/` | Cross-layer invariants, end-to-end workflow, case assessment, financial boundaries and reporting fallback |
| `tests/llm/` | Client abstractions, Gemini/Ollama clients, prompt construction and indicator grounding |
| `tests/models/` | Assessment, status, finding, position, report and workflow-result models |
| `tests/rules/` | Rule base contracts, severity, discovery/registry and individual rule implementations |
| `tests/services/` | Assessment services, domain services, validators, Excel loader, final-assessment policy and factories |

The repository also has `tests/conftest.py`, which provides the shared `assessment_service` fixture. It constructs an `AssessmentService` using the default discovered rules, `RuleEngine`, deterministic `CommentEngine` and `AssessmentStatusCalculator`.

## Unit, integration and workflow coverage

### Unit-level tests

Focused tests isolate a model, rule, service, parser, client or presentation helper. They are the preferred starting point when changing one component. Rule tests should exercise all relevant outcomes, including `TRIGGERED`, `NOT_TRIGGERED` and `NOT_EVALUABLE`, where supported by the rule contract.

### Integration tests

Tests under `tests/integration/` verify contracts across component boundaries. The current group includes:

- analysis/reporting invariants;
- end-to-end assessment workflow;
- credit-assessment case aggregation;
- financial rule/configuration boundaries;
- financial-to-final-assessment propagation;
- reporting error and deterministic-fallback behaviour.

These tests are particularly important when changing data models, evidence propagation, status aggregation or reporting contracts.

### Application tests

Tests under `tests/app/` currently focus on the in-code demo-scenario builder and selected UI data/presentation helpers. They do **not** constitute exhaustive browser-level or Streamlit interaction coverage. The current active workbook input path and overall Streamlit composition should therefore be reviewed alongside the Excel loader, workflow and integration tests when those areas change.

## LLM and provider tests

The LLM test group covers client behaviour, prompt construction, generated-output structure and evidence grounding. Provider-facing tests may use mocks to keep the default suite deterministic and independent of external services.

Ollama-dependent tests use the `ollama` pytest marker. The repository's `pyproject.toml` sets the default pytest expression to `-m 'not ollama'`, so those tests are excluded from an ordinary test run. Running them requires an available Ollama service and the relevant model/configuration. Do not interpret their default exclusion as evidence that they passed.

## Running the suite

Install dependencies first:

```bash
python -m pip install -r requirements.txt
```

Run the default test suite:

```bash
python -m pytest
```

Run with coverage for the core `src` package:

```bash
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

The coverage target in this command is `src`; it does not measure coverage of the Streamlit `app/` package. The configured minimum and CI command must be read from `.github/workflows/tests.yml`, not inferred from a historical coverage result or a README badge.

## CI quality gates

The current GitHub Actions workflow is `.github/workflows/tests.yml`. It runs on pushes and pull requests targeting `main`, sets up Python 3.14, installs `requirements.txt`, then runs:

```bash
python -m ruff check .
python -m mypy src
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

Ruff checks the repository. Mypy is scoped to `src`. Pytest runs the default marker selection and enforces the configured coverage threshold for `src`.

## Selecting tests for a change

| Change | Start with |
|---|---|
| Rule logic or severity | Relevant `tests/rules/`, then domain service/status tests |
| Rule configuration, discovery or registry | `tests/config/` and `tests/rules/` |
| Input model or validation | `tests/models/` and relevant `tests/services/` |
| Excel workbook contract | `tests/services/test_excel_scenario_loader.py` |
| Final assessment policy/rationale | `tests/config/test_final_assessment_policy.py`, `tests/services/test_final_assessment_service.py` and integration tests |
| Analysis or report structure | `tests/agents/analysis/`, `tests/agents/reporting/` and `tests/llm/` |
| Provider fallback | `tests/integration/test_reporting_error_fallback.py` and reporting-agent tests |
| Workflow construction/metadata | `tests/agents/workflow/` and end-to-end integration tests |
| Demo scenario data | `tests/app/demo/` |
| UI presentation helper | The corresponding module under `tests/app/ui/` |
| Application input or Streamlit composition | Relevant loader/workflow tests plus focused application tests; add dedicated tests when new behaviour is introduced |

## Maintenance rules

- Derive expected business outcomes from the deterministic implementation and configuration; do not duplicate decision logic in tests.
- Keep provider tests isolated with mocks unless a test is explicitly marked as requiring a live provider.
- Use synthetic data; do not introduce confidential customer or banking information.
- Test missing and partial data explicitly. Missing evidence must not silently become a normal result.
- Assert execution metadata separately from credit-decision evidence.
- Keep integration tests focused on cross-component invariants rather than duplicating every unit-level assertion.
- Update this guide when test packages, markers, fixtures or CI quality gates change.
