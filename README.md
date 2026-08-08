# Credit Assessment System

A modular and auditable credit assessment support system based on a **deterministic rule engine**, **automated commentary generation**, and **LLM/agent-based reporting**.

The system is designed as a **decision-support tool**: business rules remain explicit, deterministic, testable, and independent from any LLM component.

---

## Architecture

The core assessment flow is:

```text
CreditPosition
      ↓
   RuleEngine
      ↓
  RuleResults
      ↓
 CommentEngine
      ↓
   Comments
      ↓
  Assessment
```

The overall workflow is orchestrated by the `AssessmentService`:

```text
                     ┌─────────────────┐
                     │ CreditPosition  │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   RuleEngine    │
                     └────────┬────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              ┌──────────┐        ┌──────────┐
              │  Rule 1  │  ...   │  Rule N  │
              └────┬─────┘        └────┬─────┘
                   │                   │
                   └─────────┬─────────┘
                             ▼
                       ┌───────────┐
                       │RuleResult │
                       └─────┬─────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  CommentEngine │
                    └───────┬────────┘
                            ▼
                       ┌─────────┐
                       │ Comments│
                       └────┬────┘
                            │
                            ▼
                      ┌──────────┐
                      │Assessment│
                      └──────────┘
```

---

## Core Components

### `CreditPosition`

Represents the financial and credit information used by the assessment.

It contains **input data only** and does not implement business rules.

```text
CreditPosition
    ├── revenue_growth
    ├── EBITDA
    ├── EBITDA margin
    ├── PFN / EBITDA
    └── interest expense
```

**Responsibility:** provide the data required by the rules.

---

### `Rule`

A `Rule` represents a single piece of **credit assessment business logic**.

Each rule should have:

* a unique `rule_id`
* a descriptive `rule_name`
* a `category`
* a threshold, where applicable
* an `evaluate()` method

Example:

```python
class EbitdaMarginRule(Rule):

    rule_id = "R003"
    rule_name = "EBITDA margin deterioration"
    category = "profitability"
    threshold = 0.0

    def evaluate(self, position: CreditPosition) -> RuleResult:
        triggered = position.ebitda_margin < self.threshold

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            category=self.category,
            triggered=triggered,
            value=position.ebitda_margin,
            threshold=self.threshold,
        )
```

**Important architectural principle:**

> One class should normally represent one independent business rule.

If two indicators represent two different credit conditions, they should normally be implemented as two separate `Rule` classes, even if they belong to the same category or Python module.

---

### `RuleEngine`

The `RuleEngine` is responsible for **executing the configured rules**.

It does not contain the business logic itself.

```text
RuleEngine
    ↓
Rule 1 → RuleResult
Rule 2 → RuleResult
Rule 3 → RuleResult
...
```

**Responsibility:** execute rules and collect their results.

---

### `RuleResult`

`RuleResult` is the standardized output produced by every rule.

It contains:

* `rule_id`
* `rule_name`
* `category`
* `triggered`
* `value`
* `threshold`

This creates a consistent interface between the rule engine and the rest of the system.

```text
Rule
  ↓
RuleResult
  ├── rule_id
  ├── rule_name
  ├── category
  ├── triggered
  ├── value
  └── threshold
```

---

### `CommentEngine`

The `CommentEngine` converts triggered `RuleResult` objects into **human-readable comments**.

The comment layer should not contain the underlying credit decision logic.

For example:

```text
RuleResult
    ↓
CommentEngine
    ↓
"Revenue deterioration detected. Revenue growth: -15.0%."
```

The `CommentEngine` is therefore responsible for **interpretation and presentation**, not for determining whether a credit rule is triggered.

---

### `Comment`

Represents the human-readable explanation generated for a triggered rule.

A comment is associated with the originating rule through its `rule_id`.

```text
Rule R001
   ↓
RuleResult R001
   ↓
Comment R001
```

This maintains traceability between the business rule and the generated explanation.

---

### `AssessmentService`

`AssessmentService` is the **application-level orchestrator**.

It coordinates the complete assessment workflow:

```text
CreditPosition
      ↓
AssessmentService
      ↓
RuleEngine
      ↓
RuleResults
      ↓
CommentEngine
      ↓
Comments
      ↓
Assessment
```

It should coordinate components rather than duplicate their responsibilities.

---

## Rule Organization

Rules are grouped into modules according to their business domain.

For example:

```text
src/rules/
│
├── revenue_rules.py
├── profitability_rules.py
├── margin_rules.py
├── leverage_rules.py
└── financial_expenses_rules.py
```

A module may contain **multiple related rules**.

For example:

```text
profitability_rules.py

    NegativeEbitdaRule
    NetLossRule
    ...
```

The important distinction is:

> **One module can contain multiple related rules, but each independent business rule should normally have its own class.**

---

## Rule Registration

The rules used by the application are explicitly registered in the configuration layer.

```text
config/rules.py
        ↓
DEFAULT_RULES
        ↓
RuleEngine
```

This makes the active rule set explicit and easily auditable.

Adding a new rule generally requires:

1. Create the `Rule` class.
2. Define its `rule_id`.
3. Implement `evaluate()`.
4. Add unit tests.
5. Register the rule in `DEFAULT_RULES`.
6. Add the corresponding comment template.
7. Add or update integration tests where necessary.

---

## Testing Philosophy

The system follows a layered testing approach.

```text
Unit Tests
    ↓
Individual Rules
    ↓
RuleEngine
    ↓
CommentEngine
    ↓
AssessmentService
    ↓
Integration Behaviour
```

Each business rule should be tested for at least:

* triggered condition
* non-triggered condition
* boundary conditions
* missing or invalid input where relevant

The objective is to keep the assessment logic **deterministic, reproducible, and auditable**.

---

## Design Principles

### 1. Separation of responsibilities

Each component should have a single clear responsibility.

```text
CreditPosition  → data
Rule            → business logic
RuleEngine      → execution
RuleResult      → standardized output
CommentEngine   → interpretation
Comment         → human-readable output
AssessmentService → orchestration
```

### 2. Deterministic business logic

Credit assessment rules must remain explicit and deterministic.

The same input data and rule configuration should produce the same `RuleResult`.

### 3. Traceability

Every result and comment must remain traceable to its originating `rule_id`.

```text
R001
 ↓
Rule
 ↓
RuleResult
 ↓
Comment
```

### 4. Testability

Rules should be independently testable without requiring the entire application.

### 5. Modularity

New rules should be addable without modifying unrelated components.

### 6. LLM separation

The deterministic rule engine is independent from the LLM/reporting layer.

The LLM should operate on structured assessment outputs rather than replacing the underlying credit assessment logic.

```text
                 Deterministic Layer
                       │
CreditPosition → RuleEngine → Assessment
                                      │
                                      ▼
                              Reporting / LLM
```

The LLM is therefore used for **report generation and narrative organization**, while the underlying credit assessment remains based on explicit and auditable rules.

---

## Project Objective

The objective of the project is to provide a prototype architecture for a **transparent, modular, and auditable credit assessment support system**.

The architecture is designed to allow:

* rapid addition of new credit rules
* independent testing of business logic
* traceability from input data to assessment output
* automated generation of explanatory comments
* future integration with an LLM-based reporting layer
* separation between deterministic assessment logic and generative reporting
