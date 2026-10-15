# Excel scenario input

The application supports scenario-driven assessment through a structured Excel workbook. Uploaded data are validated and transformed into the same domain models used by the native application.

This keeps the deterministic assessment engine independent from the data-ingestion layer:

`Excel workbook → validation/mapping → domain models → assessment workflow → deterministic rules → analysis/reporting`

## Workbook structure

A workbook must contain:

- `Financial Analysis` — required, one row per scenario
- `Customer Profile` — optional, one row per scenario
- `Behavioural Analysis` — optional, one row per scenario
- `Debt Sustainability` — optional, one row per scenario
- `Shareholders` — optional, multiple rows per scenario are allowed
- `Relevant Events` — optional, multiple rows per scenario are allowed
- `Credit Facilities` — optional, one row per individual credit line

Every sheet requires a `scenario_id` column. The same identifier connects records to the scenario in `Financial Analysis`. The four assessment-domain sheets remain one-row-per-scenario; the three detail sheets are one-to-many and intentionally support repeated `scenario_id` values. A scenario may omit an optional domain sheet; in that case the corresponding domain object is unavailable and the assessment records the domain as `NOT_EVALUABLE` rather than treating missing data as a normal observation.

### Shareholders, Relevant Events and Credit Facilities

These are detail sheets, not assessment domains. Their records are attached to the matching `Customer Profile` context for reporting. Multiple records for the same scenario are preserved individually and rendered as separate detail entries.

`Shareholders` accepts `shareholder_name`, `age`, `role` and `ownership_percentage`, in addition to `scenario_id`.

`Relevant Events` accepts `event_type`, `event_date`, `description` and `status`, in addition to `scenario_id`. Use one row per event, for example a protest, adverse legal event or restructuring. Distinguish a confirmed absence of events from an unprovided or incomplete event register.

`Credit Facilities` accepts `facility_id`, `facility_type`, `description`, `approved_amount`, `used_amount`, `cash_approved_amount`, `cash_used_amount`, `residual_debt`, `maturity_date`, `review_date`, `unpaid_installments` and `forborne`, in addition to `scenario_id`. Enter one row per credit line. Use the fields applicable to the facility type; leave non-applicable fields blank rather than entering zero. For self-liquidating facilities, use the cash-specific approved and used fields when reporting cash limits and utilisation.

### Financial Analysis

The `Financial Analysis` sheet contains the fields of `CreditPosition`, except `position_id`. The loader derives `position_id` directly from `scenario_id`, so the workbook does not need a separate position identifier.

Examples:

| scenario_id | revenue | ebitda | revenue_growth |
|---|---:|---:|---:|
| TEST-001 | 1000000 | 100000 | 0.05 |

Numeric values use the same representation as the Python domain model. For example, a 5% growth rate is entered as `0.05`.

The Financial Analysis sheet accepts the financial input fields defined by `CreditPosition` (excluding `position_id`, which is derived from `scenario_id`). This contract evolves with the model; use the model and loader validation as the authoritative field inventory rather than relying on a duplicated list in this document.

Financial rules are configured in the applicable YAML catalogue under `config/` and implemented under `src/rules/`. The configuration defines declarative inputs, calculation method, trigger operator, threshold and severity bands where applicable. A rule may also implement specialised validation or calculations in Python. Consequently, this guide intentionally avoids maintaining a paragraph for every rule and threshold.

When adding or changing financial indicators:

- add any new input fields to `CreditPosition`;
- use consistent units, currency and reporting periods for related inputs;
- document the business meaning and calculation contract for non-obvious fields;
- ensure missing or invalid evidence results in `NOT_EVALUABLE` where the calculation cannot be performed safely;
- update the configuration, implementation and focused tests together;
- update the reference workbook's Financial Analysis headers and representative scenario values when the input contract changes.

For ratios, provide a valid denominator and test zero/negative denominator handling. Historical comparisons require observations to use a consistent annual basis and comparable accounting definitions. Growth-gap indicators compare percentage changes over the same period; they should not be interpreted as proof of collection distress without considering seasonality, business mix and payment terms. Thresholds are policy parameters and should be calibrated to the business context; a triggered indicator is a warning signal, not by itself a complete credit judgement.

### Customer Profile

The sheet contains the fields of `CustomerProfileData`.

List-valued fields are entered as semicolon-separated values:

`Revenue deterioration;Payment delay`

The regulatory risk-grade fields accept only:

- `Bonis`
- `Past Due`
- `Unlikely to Pay`
- `Bad Loan`

The EWS class accepts:

- `GREEN`
- `YELLOW`
- `ORANGE`
- `LIGHT_RED`

### Behavioural

The sheet contains the fields of `BehaviouralData`:

| Field | Meaning |
|---|---|
| `average_utilization` | Average utilisation of available credit facilities |
| `overdraft_days` | Number of days with overdraft usage |
| `payment_delay_days` | Payment-delay indicator expressed in days |
| `exposure_growth` | Exposure growth rate |
| `cr_reference_date` | Date of the latest available Centrale dei Rischi data, in `YYYY-MM-DD` format (for example, `2026-09-30`) |
| `total_utilized_system` | Total utilized exposure at system level, in euros |
| `utilized_revocable` | Utilized amount for revocable credit lines, in euros |
| `utilized_term` | Utilized amount for term facilities, in euros |
| `utilized_self_liquidating` | Utilized amount for self-liquidating facilities, in euros |

The reference workbook keeps these inputs deliberately neutral across the three demonstration scenarios:

| scenario_id | average_utilization | overdraft_days | payment_delay_days | exposure_growth |
|---|---:|---:|---:|---:|
| DEMO-NORMAL | 0.50 | 2 | 5 | 0.05 |
| DEMO-ATTENTION | 0.50 | 2 | 5 | 0.05 |
| DEMO-CRITICAL | 0.50 | 2 | 5 | 0.05 |

This is intentional: the scenarios isolate differences in the financial assessment rather than introduce additional behavioural triggers. The integrated demo case can also include synthetic CR context fields; these are descriptive only and do not affect rule evaluation.

### Debt Sustainability

The sheet contains the fields of `DebtSustainabilityData`.

## Reference demo scenarios

The reference Excel artifact is the application-facing demonstration input. Scenario rows can be extended or replaced without changing the deterministic assessment architecture, provided the workbook contract is preserved.

| Scenario | Intended behaviour |
|---|---|
| `DEMO-NORMAL` | baseline case without significant financial deterioration |
| `DEMO-ATTENTION` | isolated MEDIUM financial deterioration |
| `DEMO-CRITICAL` | multiple HIGH financial deterioration indicators |

The workbook also contains a `README` sheet documenting the workbook contract and scenario purpose. Its formatting (tables, filters, frozen headers, widths and number formats) is presentation-only and does not affect ingestion.

Scenario data are demonstration-only and may include integrated Customer Profile, Behavioural and Debt Sustainability context. Their values are illustrative and do not constitute production banking data.

## Validation

The loader validates:

- required workbook sheets;
- presence of `scenario_id`;
- duplicate scenario identifiers;
- scenario identifiers that do not exist in `Financial Analysis`;
- unsupported columns;
- numeric and integer values;
- conversion of Excel numeric cells to the numeric Python types expected by the domain models;
- boolean values;
- EWS score classes;
- regulatory risk-grade categories.

Blank cells are mapped to `None` for scalar fields and empty lists for list-valued fields.

Validation errors are shown in the Streamlit interface before the assessment can be executed.

## Streamlit workflow

Upload an `.xlsx` workbook, select one of the loaded scenarios, review the mapped inputs, and run the assessment. Excel Upload is the only application data source.

The selected workbook scenario follows the assessment workflow directly. The Excel layer does not evaluate rules or alter thresholds/statuses.

## Design boundary

The Excel loader is an ingestion adapter. It is intentionally separate from:

- the deterministic Rule Engine;
- rule configuration;
- assessment status calculation;
- LLM analysis and reporting.

This separation allows the workbook format to evolve without changing the rule-evaluation layer.
