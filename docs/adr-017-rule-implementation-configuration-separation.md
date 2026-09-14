# ADR-017: Separate Rule Implementation from Rule Configuration

## Status

Accepted

## Context

The assessment catalog contains 17 deterministic rules across four domains:

- Customer Profile: `CP001–CP003`
- Financial Analysis: `R001–R007`
- Behavioural Analysis: `B001–B004`
- Debt Sustainability: `DS001–DS003`

The YAML catalogs already define thresholds, operators, severity policy and comment templates. Previously, however, the non-financial domains still contained duplicated rule-evaluation logic inside their assessment services.

That created two competing implementation paths:

```text
Financial rules → src/rules/* → RuleEngine
Other domains   → service-local evaluation logic
```

This made the rule registry incomplete from an implementation perspective and allowed the same deterministic policy to be expressed in multiple places.

## Decision

Adopt a strict two-layer rule architecture:

```text
config/*.yaml
    │
    │ configuration
    ▼
src/rules/
    │
    │ implementation
    ▼
Rule Registry
    │
    ▼
Domain Assessment Services / Rule Engine
```

### `src/rules/`

Contains the executable deterministic rule implementations and their registration with `Rule`.

Current domain packages include:

```text
src/rules/
├── base/
├── financial/
├── customer_profile/
│   └── rules.py
├── behavioural/
│   └── rules.py
└── sustainability/
    └── rules.py
```

The new domain implementations delegate threshold comparison, severity resolution, calculations and result construction to the common `Rule` base behaviour.

### `config/`

Contains declarative rule metadata:

- rule identifier;
- name and category;
- input field(s);
- calculation type;
- trigger operator;
- threshold;
- severity;
- severity direction;
- severity bands;
- comment template.

Configuration therefore controls **parameters**, while Python controls **rule execution**.

## Consequences

### Positive

- Every configured rule has a concrete registered implementation.
- Domain services no longer duplicate threshold/comparison/severity logic.
- Rule behaviour has a single deterministic implementation path.
- Thresholds can be changed without changing Python rule code.
- Rule discovery and registry validation can detect missing implementations.
- The architecture remains compatible with the deterministic-first AI boundary.

### Constraint

The existing `get_default_rules()` remains the financial/core catalog used by the financial `RuleEngine`. Domain services load their own YAML catalog and resolve implementations through the same shared registry. A future unified multi-domain engine can therefore be introduced without another rule-model migration.

## Validation

The configuration test suite now verifies that every rule present in the complete YAML catalog has a registered Python implementation.

The architectural invariant is:

```text
Every configured rule_id
        ↓
registered Rule implementation
        ↓
deterministic RuleResult
```

No LLM component participates in this path.
