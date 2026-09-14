# ADR-017: Separate Rule Implementation from Rule Configuration

## Status

Accepted

## Context

The assessment catalogue evolves independently of the application architecture. Rule parameters such as thresholds, operators, severity policy and comments are policy/configuration concerns, while deterministic evaluation is implementation logic.

Keeping the active rule inventory, identifiers and thresholds duplicated in architecture documentation would create a second source of truth and make the documentation stale whenever the catalogue changes.

A second maintainability concern is rule isolation: individual rules can become substantially more complex over time. Keeping unrelated rules in shared modules increases coupling and makes rule-specific testing and review harder.

## Decision

Adopt a strict separation between rule configuration and deterministic rule implementation, with one concrete implementation module per rule in the normal case.

```text
config/<domain>_rules.yaml
          ↓
   RuleConfigLoader
          ↓
   Rule configuration
          ↓
 Automatic rule discovery
          ↓
      Rule registry
          ↓
 configured rule_id
          ↓
 Concrete Rule implementation
          ↓
       RuleResult
          ↓
RuleEngine / domain service
```

The documentation does not enumerate the active rule inventory. The YAML catalogues and registered implementations are authoritative.

## Rule implementation

Rules live below the rule package, organised by domain. A concrete rule module inherits from the shared `Rule` abstraction and registers its identifier:

```python
@Rule.register("RXXX")
class ExampleRule(Rule):
    ...
```

The identifier must match the configured `rule_id` exactly.

The normal extension mechanism does not require a central import list. Rule discovery recursively imports rule modules, allowing the registry to be populated from the implementation package.

The module structure should mirror the domain structure used by the repository, but documentation should not hard-code every current filename because those modules are expected to evolve.

## Configuration

YAML configuration contains declarative rule metadata, including where applicable:

- rule identifier;
- name and category;
- input field(s);
- calculation type;
- trigger operator;
- threshold;
- severity;
- severity direction;
- severity thresholds/bands;
- comment template.

Configuration controls **parameters**. Python controls **execution and specialised business semantics**.

The generic configuration contract should be preferred whenever it can express the business requirement. Specialised Python logic is justified when the rule requires semantics that cannot be safely represented by the generic calculation/trigger contract.

## Discovery and registry

The registry provides the mapping:

```text
configured rule_id
       ↓
registered Rule class
       ↓
Rule instance configured with RuleConfig
```

The architectural invariant is:

```text
Every valid configured rule identifier
            ↓
exactly one resolvable deterministic implementation
```

A missing implementation or duplicate registration must fail explicitly rather than silently excluding the rule.

## Separation of responsibilities

### Rule implementation

Owns:

- deterministic evaluation;
- specialised calculations;
- interpretation of required inputs;
- production of `RuleResult`.

Does not own:

- final case status;
- other rules;
- Streamlit presentation;
- LLM calls.

### Configuration

Owns policy parameters that can safely be externalised.

### Rule engine / domain service

Owns execution and section-level aggregation, not individual rule semantics.

### Final assessment service

Owns cross-section aggregation using the configured final-assessment policy.

### Analysis/reporting

Owns interpretation and narrative generation from structured deterministic evidence. It must not reimplement rule logic.

### Presentation

Owns rendering only. It must not recalculate business decisions.

## Adding a rule

A complete change follows:

```text
Business requirement
       ↓
Input contract
       ↓
Configuration
       ↓
Rule implementation
       ↓
Discovery / registry
       ↓
RuleResult
       ↓
Section / case aggregation
       ↓
Analysis evidence
       ↓
Reporting / grounding
       ↓
Demo / UI
       ↓
Tests
```

The full operational checklist is maintained in [`rules.md`](rules.md).

## Consequences

### Positive

- Policy parameters can evolve without changing central services.
- New rules do not require central rule-specific branching.
- Individual rules remain independently testable and reviewable.
- The active catalogue is not duplicated in documentation.
- Complex rules can grow their own internal helpers without affecting unrelated rules.
- The architecture remains compatible with deterministic-first AI reporting.

### Constraints

- Every configured identifier must have a registered implementation.
- Rule configuration and implementation must be kept semantically aligned.
- Specialised rule code must remain deterministic.
- Configuration changes require corresponding boundary and integration tests.
- Catalogue-specific examples in documentation must be clearly marked as examples.

## Validation

Configuration and registry tests should verify that the active catalogue can be resolved completely.

Rule tests should cover positive, negative, boundary, severity, non-evaluable and calculation edge cases. Integration tests should verify propagation into section/case evidence and reporting.

No LLM component participates in deterministic rule registration or evaluation.
