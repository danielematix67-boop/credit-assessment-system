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

The sheet contains the fields of `BehaviouralData`.

### Debt_Sustainability

The sheet contains the fields of `DebtSustainabilityData`.

## Validation

The loader validates:

- required workbook sheets;
- presence of `scenario_id`;
- duplicate scenario identifiers;
- scenario identifiers that do not exist in `Credit_Position`;
- unsupported columns;
- numeric and integer values;
- boolean values;
- EWS score classes;
- regulatory risk-grade categories.

Blank cells are mapped to `None` for scalar fields and empty lists for list-valued fields.

Validation errors are shown in the Streamlit interface before the assessment can be executed.

## Streamlit workflow

Select **Excel Upload** as the data source, upload an `.xlsx` workbook, select one of the loaded scenarios, review the mapped inputs, and run the assessment.

The uploaded scenario follows the same assessment workflow as the native demo scenario. The Excel layer does not evaluate rules or alter thresholds/statuses.

## Design boundary

The Excel loader is an ingestion adapter. It is intentionally separate from:

- the deterministic Rule Engine;
- rule configuration;
- assessment status calculation;
- LLM analysis and reporting.

This separation allows the workbook format to evolve without changing the rule-evaluation layer.
