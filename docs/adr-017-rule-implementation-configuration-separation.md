# ADR-017: Separate Rule Implementation from Rule Configuration

## Status

Accepted

## Context

The assessment catalog contains **18 deterministic rules across four domains**:

- Customer Profile: `CP001–CP004`
- Financial Analysis: `R001–R007`
- Behavioural Analysis: `B001–B004`
- Debt Sustainability: `DS001–DS003`

The YAML catalogs define thresholds, operators, severity policy and comment templates. Rule implementation is maintained in Python and must remain the deterministic source of truth.

A second architectural concern is maintainability: individual rules may become substantially more complex over time. Keeping multiple rules in a single `rules.py` module would create large, coupled files and make rule-specific testing and evolution harder.

## Decision

Adopt a strict separation between rule configuration and rule implementation, with **one Python module per concrete rule**, using the same structure for every assessment domain.

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

Every assessment domain follows the same layout. There are no domain-level `rules.py` aggregation modules and no special financial rule structure.

```text
src/rules/
├── base/
├── customer_profile/
│   ├── cp001.py
│   ├── cp002.py
│   ├── cp003.py
│   └── cp004.py
├── financial_analysis/
│   ├── r001.py
│   ├── r002.py
│   ├── r003.py
│   ├── r004.py
│   ├── r005.py
│   ├── r006.py
│   └── r007.py
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

The rule identifier is deliberately reflected in the module name. This creates a direct mapping between configuration, implementation and tests:

```text
R001 → config → src/rules/financial_analysis/r001.py → test
B001 → config → src/rules/behavioural/b001.py        → test
DS001 → config → src/rules/sustainability/ds001.py   → test
```

A simple rule remains a single file. If a rule becomes substantially more complex, its module can evolve into a dedicated package without changing the registry or assessment-service contract, for example:

```text
src/rules/financial_analysis/r005/
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

Configuration therefore controls **parameters**, while Python controls **rule execution and specialised business semantics**.

### Tests

Rule-specific tests should mirror the same domain/identifier structure:

```text
tests/rules/
├── customer_profile/
│   ├── test_cp001.py
│   └── ...
├── financial_analysis/
│   ├── test_r001.py
│   └── ...
├── behavioural/
│   ├── test_b001.py
│   └── ...
└── sustainability/
    ├── test_ds001.py
    └── ...
```

Tests should cover triggered, not-triggered, boundary, severity, missing/invalid input, calculation edge cases and deterministic evidence. Configuration/registry tests must also ensure that configured rules have registered implementations.

## New Rule Change Path

A complete rule change follows this path:

```text
Business requirement
       ↓
CreditPosition input field(s)
       ↓
Domain YAML configuration
       ↓
Concrete Rule implementation
       ↓
Automatic discovery + registry
       ↓
RuleEngine / Domain Assessment Service
       ↓
RuleResult
       ↓
Deterministic analysis
       ↓
Reporting + grounding validation
       ↓
Results UI
       ↓
Tests + demo scenarios + documentation
```

The rule itself owns deterministic business semantics. Aggregation, reporting and presentation must remain outside the rule.

## Consequences

### Positive

- All four domains use one consistent rule architecture.
- Every configured rule has one concrete registered implementation.
- Each rule can evolve independently without enlarging a shared `rules.py` file.
- Complex rules can gain private helper modules without affecting other rules.
- Domain services do not duplicate threshold/comparison/severity logic.
- Rule behaviour has a single deterministic implementation path.
- Thresholds can be changed without changing Python rule code when the generic rule semantics are sufficient.
- Rule discovery and registry validation can detect missing implementations.
- Rule-specific tests remain focused and easy to locate.
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
