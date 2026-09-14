# ADR-017: Separate Rule Implementation from Rule Configuration

## Status

Accepted

## Context

The assessment catalog contains 17 deterministic rules across four domains:

- Customer Profile: `CP001–CP003`
- Financial Analysis: `R001–R007`
- Behavioural Analysis: `B001–B004`
- Debt Sustainability: `DS001–DS003`

The YAML catalogs define thresholds, operators, severity policy and comment templates. Rule implementation is maintained in Python and must remain the deterministic source of truth.

A second architectural concern is maintainability: individual rules may become substantially more complex over time. Keeping multiple rules in a single `rules.py` module would create large, coupled files and make rule-specific testing and evolution harder.

## Decision

Adopt a strict separation between rule configuration and rule implementation, with **one Python module per concrete rule**.

```text
config/*.yaml
    │
    │ configuration / parameters
    ▼
src/rules/<domain>/<rule>.py
    │
    │ deterministic implementation
    ▼
Rule Registry
    │
    ▼
Rule Engine / Domain Assessment Service
```

### `src/rules/`

Contains executable deterministic rule implementations. Each concrete rule has its own module and registers itself with `Rule`.

The target structure is:

```text
src/rules/
├── base/
├── financial/
│   ├── revenue/
│   │   └── revenue_growth.py
│   ├── margins/
│   ├── profitability/
│   └── leverage/
├── customer_profile/
│   ├── cp001.py
│   ├── cp002.py
│   └── cp003.py
├── behavioural/
│   ├── b001.py
│   ├── b002.py
│   ├── b003.py
│   └── b004.py
└── sustainability/
    ├── ds001.py
    ├── ds002.py
    └── ds003.py
```

Financial rules may retain a meaningful business subdomain grouping where that grouping already exists. The important invariant is that each concrete rule implementation remains independently maintainable and discoverable.

A simple rule can remain a single file. If a rule becomes substantially more complex, its module can evolve into a dedicated package without changing the registry or assessment-service contract, for example:

```text
src/rules/financial/r005/
├── __init__.py
├── rule.py
├── calculations.py
└── validators.py
```

Rule discovery recursively imports rule modules, so adding a new rule does not require a central list of imports.

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

### Tests

Rule-specific tests should mirror the implementation structure where practical:

```text
tests/rules/
├── customer_profile/
│   ├── test_cp001.py
│   └── ...
├── behavioural/
│   ├── test_b001.py
│   └── ...
└── sustainability/
    ├── test_ds001.py
    └── ...
```

## Consequences

### Positive

- Every configured rule has a concrete registered implementation.
- Each rule can evolve independently without enlarging a shared `rules.py` file.
- Complex rules can gain private helper modules without affecting other rules.
- Domain services no longer duplicate threshold/comparison/severity logic.
- Rule behaviour has a single deterministic implementation path.
- Thresholds can be changed without changing Python rule code.
- Rule discovery and registry validation can detect missing implementations.
- Rule-specific tests can remain focused and easy to locate.
- The architecture remains compatible with the deterministic-first AI boundary.

### Constraint

The existing `get_default_rules()` remains the financial/core catalog used by the financial `RuleEngine`. Domain services load their own YAML catalog and resolve implementations through the same shared registry. A future unified multi-domain engine can therefore be introduced without another rule-model migration.

## Validation

The configuration test suite verifies that every rule present in the complete YAML catalog has a registered Python implementation.

The architectural invariant is:

```text
Every configured rule_id
        ↓
one concrete registered Rule implementation
        ↓
deterministic RuleResult
```

No LLM component participates in this path.
