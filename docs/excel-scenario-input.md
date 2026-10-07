# Excel scenario input

The application supports scenario-driven assessment through a structured Excel workbook. Uploaded data are validated and transformed into the same domain models used by the native application.

This keeps the deterministic assessment engine independent from the data-ingestion layer:

`Excel workbook → validation/mapping → domain models → assessment workflow → deterministic rules → analysis/reporting`

## Workbook structure

A workbook must contain:

- `Credit_Position` — required
- `Customer_Profile` — optional
- `Behavioural` — optional
- `Debt_Sustainability` — optional

Each sheet contains one row per scenario and a mandatory `scenario_id` column. The same `scenario_id` identifies the case across sheets.

### Credit_Position

The `Credit_Position` sheet contains the fields of `CreditPosition`, except `position_id`. The loader derives `position_id` from `scenario_id`.

Examples:

| scenario_id | revenue | ebitda | revenue_growth |
|---|---:|---:|---:|
| TEST-001 | 1000000 | 100000 | 0.05 |

Numeric values use the same representation as the Python domain model. For example, a 5% growth rate is entered as `0.05`.

### Customer_Profile

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

The reference workbook keeps these inputs deliberately neutral across the three demonstration scenarios:

| scenario_id | average_utilization | overdraft_days | payment_delay_days | exposure_growth |
|---|---:|---:|---:|---:|
| DEMO-NORMAL | 0.50 | 2 | 5 | 0.05 |
| DEMO-ATTENTION | 0.50 | 2 | 5 | 0.05 |
| DEMO-CRITICAL | 0.50 | 2 | 5 | 0.05 |

This is intentional: the scenarios isolate differences in the financial assessment rather than introduce additional behavioural triggers.

### Debt_Sustainability

The sheet contains the fields of `DebtSustainabilityData`.

## Reference demo scenarios

The reference workbook `examples/excel/demo_scenarios.xlsx` contains the end-to-end synthetic demonstration case(s) used by the application:

| Scenario | Intended behaviour |
|---|---|
| `DEMO-NORMAL` | baseline case without significant financial deterioration |
| `DEMO-ATTENTION` | isolated MEDIUM financial deterioration |
| `DEMO-CRITICAL` | multiple HIGH financial deterioration indicators |

The workbook also contains a `README` sheet documenting the workbook contract and scenario purpose. Its formatting (tables, filters, frozen headers, widths and number formats) is presentation-only and does not affect ingestion.

Customer Profile and Behavioural inputs are intentionally stable across the scenarios. Financial inputs are varied to make the deterministic assessment outcomes easy to inspect.

## Validation

The loader validates:

- required workbook sheets;
- presence of `scenario_id`;
- duplicate scenario identifiers;
- scenario identifiers that do not exist in `Credit_Position`;
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
