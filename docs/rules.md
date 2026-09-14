# Rule Development Guide

This document describes the complete lifecycle of a deterministic assessment rule.

The guide is intentionally **catalogue-independent**: the active rule set is discovered from the configuration and registry at runtime. Documentation should not need to be rewritten merely because a rule is added, removed or renamed. Only architectural changes, policy changes or examples that become inaccurate require documentation updates.

## Source of truth

A rule is the result of three coordinated artefacts:

```text
Domain configuration
       +
Concrete Rule implementation
       +
Registered rule identifier
       ↓
Deterministic RuleResult
```

The YAML catalogue is the source of truth for declarative rule parameters. The Python implementation is the source of truth for deterministic execution and specialised business semantics. The registry is the source of truth for resolving a configured identifier to an implementation.

No LLM component is part of this chain.

## Rule lifecycle

```text
Business requirement
        ↓
Input contract
        ↓
Rule configuration
        ↓
Rule implementation
        ↓
Automatic discovery
        ↓
Registry resolution
        ↓
RuleEngine / domain service
        ↓
RuleResult
        ↓
Section assessment
        ↓
Case aggregation
        ↓
Analysis evidence
        ↓
Reporting / grounding
        ↓
Presentation
        ↓
Tests + demo + documentation
```

A rule is complete only when the whole path is coherent.

## 1. Define the business requirement

Before writing code, define the rule independently of its implementation:

- stable identifier and naming convention;
- assessment domain;
- business meaning and credit-risk rationale;
- required source data;
- calculation semantics;
- trigger condition;
- threshold(s);
- severity policy;
- treatment of missing or invalid evidence;
- deterministic explanation/evidence expected by an analyst.

Define expected behaviour for at least three states:

```text
TRIGGERED
NOT_TRIGGERED
NOT_EVALUABLE
```

Do not use a rule to encode case-level aggregation policy. A rule evaluates its own condition; section and case services aggregate the results.

## 2. Check the input model

Every configured input must be represented by the domain input contract used by the assessment workflow.

If a new field is needed:

1. add it to the appropriate model;
2. choose an explicit type;
3. decide whether absence is represented by `None`;
4. update structural validation if necessary;
5. update input/demo handling where the field is exposed;
6. add model/validation tests.

`None` should remain distinguishable from a valid numeric or boolean value when missing evidence has credit-significance. Structural validation and business-rule validation are separate concerns.

## 3. Add configuration

Rule catalogues live under `config/` and are loaded by `RuleConfigLoader`.

A generic direct-value rule can use the following shape:

```yaml
- rule_id: RXXX
  rule_name: Example rule
  indicator: Example indicator
  category: example_category
  input_field: example_value
  trigger_operator: LT
  threshold: 0.0
  severity: MEDIUM
  severity_direction: LOWER_IS_WORSE
  comment_template: >-
    Example indicator is {value}, with threshold {threshold}.
```

For a calculation using two inputs:

```yaml
input_fields:
  - numerator_field
  - denominator_field
calculation: ratio
```

The generic calculation contract supports `direct`, `ratio` and `difference`. Trigger operators are `GT`, `GTE`, `LT` and `LTE`. Severity values and severity direction are represented by the domain enums/configuration contract.

Use the generic configuration path whenever the business semantics are expressible through it. Do not add Python branches solely to duplicate configurable thresholds or comparison operators.

## 4. Implement the rule

Create a concrete module under the package corresponding to the assessment domain. The filename should reflect the rule identifier.

The class must inherit from `Rule` and register the same identifier used by configuration:

```python
from typing import Any

from src.rules.base.rule import Rule
from src.rules.base.status import RuleStatus
from src.rules.result import RuleResult


@Rule.register("RXXX")
class ExampleRule(Rule):
    def evaluate(self, position: Any) -> RuleResult:
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

The base `Rule` abstraction provides reusable behaviour for configured values, trigger operators, severity, reason formatting and `NOT_EVALUABLE` results. Specialised rules may override `evaluate()` when the business calculation cannot be expressed by the generic configuration contract.

### Implementation rules

- Do not calculate final case status inside a rule.
- Do not access Streamlit from a rule.
- Do not call an LLM from a rule.
- Do not duplicate YAML thresholds in Python unless they are genuinely part of specialised business semantics.
- Do not silently convert missing evidence into a normal value.
- Return a deterministic `RuleResult` for every input state.
- Keep the rule implementation side-effect free.

## 5. Discovery and registry

Concrete rule modules are automatically discovered under the rule package and self-register through `@Rule.register(...)`.

The normal extension path therefore does **not** require a central list of imports:

```text
new_rule.py
    ↓
@Rule.register("RXXX")
    ↓
discover_rules()
    ↓
Rule registry
    ↓
configured rule_id
    ↓
Rule class
```

The configuration/registry invariant is:

```text
Every configured rule identifier
            ↓
exactly one resolvable deterministic implementation
```

A new rule must not be silently ignored because its implementation is missing.

## 6. Rule result and evidence

`RuleResult` is the deterministic boundary object. It carries the rule identity, category, evaluated value where available, threshold, status, severity, reason, direction and configured comment information.

The result must preserve the distinction between:

- `TRIGGERED`: the configured risk condition is satisfied;
- `NOT_TRIGGERED`: the rule was evaluated and the condition is not satisfied;
- `NOT_EVALUABLE`: required evidence was unavailable or invalid for the rule.

This distinction must survive section aggregation, case analysis and reporting.

## 7. Section and case aggregation

The rule must be tested in the context of the section that contains it. Adding a rule can change the section status because status is derived from its rule results.

The final assessment is then produced by `FinalAssessmentService` using `FinalAssessmentPolicy` loaded from configuration.

The exact aggregation policy is therefore **not a documentation constant**. If the policy changes, update `config/final_assessment.yaml` and the policy tests first; then update the architecture documentation describing the policy conceptually.

This separation allows a rule to be added without embedding knowledge of unrelated sections or the final decision policy into the rule itself.

## 8. Analysis and reporting

After deterministic assessment, analysis aggregates rule evidence for reporting.

A new rule must be visible through the same evidence path as existing rules. Reporting must consume the aggregate evidence rather than contain a special case for the new rule.

The LLM boundary is strict:

```text
Deterministic RuleResult
        ↓
Deterministic Analysis
        ↓
Reporting input
        ↓
LLM / deterministic generator
        ↓
Grounding validation
        ↓
Report
```

The reporting layer may explain evidence, but cannot change the rule status, severity, threshold, limitations or final assessment.

If the rule exposes material numeric evidence, add or update grounding tests so generated narrative cannot substitute a different value.

## 9. Demo scenarios and UI

If the rule introduces new required inputs, update synthetic/anonymized demo scenarios so the application can exercise the new path.

Prefer scenario coverage that demonstrates meaningful combinations of outcomes rather than one scenario per rule when that would create redundant data.

The Streamlit UI should render the assessment produced by the workflow. It must not duplicate rule thresholds, comparisons or status logic.

## 10. Tests

Add focused rule tests in the corresponding `tests/rules/` package.

At minimum verify:

| Area | Required check |
|---|---|
| Positive path | Condition triggers as intended |
| Negative path | Condition does not trigger when it should not |
| Boundary | Exact threshold follows the configured operator |
| Severity | Severity follows the configured policy/bands |
| Missing evidence | Returns `NOT_EVALUABLE` |
| Invalid evidence | Fails safely and deterministically |
| Calculation | Formula is correct, including edge cases |
| Evidence | Result contains the expected deterministic facts |
| Registration | Configured identifier resolves to the implementation |
| Integration | Rule reaches the correct section/case evidence |
| Reporting | Evidence survives the reporting boundary |

For ratio rules, explicitly test a zero denominator. For rules with multiple severity bands, test every meaningful boundary.

## 11. Quality gate

Run the same checks used by the repository CI before merging:

```bash
python -m ruff check .
python -m mypy src
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

A new rule should not be considered complete if only its unit tests pass while registration, integration, reporting or documentation is stale.

## 12. Documentation maintenance

The documentation should describe **contracts and mechanisms**, not maintain a manually duplicated rule inventory.

Avoid statements such as:

```text
There are N rules.
Rule IDs are A001–A004.
Domain X contains exactly N rules.
```

unless the statement is explicitly labelled as an example or historical baseline.

Prefer:

```text
Rules are loaded from the domain catalogues under config/.
The active inventory is the set of valid configured identifiers with registered implementations.
```

If a concrete rule is shown in an example, label it as an example (`RXXX`, `EXAMPLE_RULE`) rather than using a production identifier. This prevents future rule additions from making the documentation appear stale.

## Change checklist

Before merging a new rule:

- [ ] Business requirement defined.
- [ ] Input model updated, if required.
- [ ] Structural validation updated, if required.
- [ ] YAML configuration added and validated.
- [ ] Concrete rule implementation added.
- [ ] Rule registered with the configured identifier.
- [ ] Automatic discovery resolves the rule.
- [ ] Unit tests cover positive, negative, boundary and non-evaluable paths.
- [ ] Severity/calculation edge cases tested.
- [ ] Section aggregation tested where behaviour changes.
- [ ] Final-assessment impact tested where applicable.
- [ ] Deterministic evidence reaches analysis/reporting.
- [ ] Grounding tests updated where numeric evidence is material.
- [ ] Demo scenarios updated if required.
- [ ] UI verified without duplicating business logic.
- [ ] Full lint/type/test/coverage gate passes.
- [ ] Documentation updated only where architecture, policy or examples changed.
