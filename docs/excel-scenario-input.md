# Excel scenario input

The application supports scenario-driven assessment through a structured Excel workbook. Uploaded data are validated and transformed into the same domain models used by the native application.

This keeps the deterministic assessment engine independent from the data-ingestion layer:

`Excel workbook → validation/mapping → domain models → assessment workflow → deterministic rules → analysis/reporting`

## Workbook structure

A workbook must contain:

- `Financial Analysis` — required
- `Customer Profile` — optional
- `Behavioural Analysis` — optional
- `Debt Sustainability` — optional

Each sheet contains one row per scenario and a mandatory `scenario_id` column. The same `scenario_id` identifies the case across sheets. A scenario may omit an optional domain sheet; in that case the corresponding domain object is unavailable and the assessment records the domain as `NOT_EVALUABLE` rather than treating missing data as a normal observation.

### Financial Analysis

The `Financial Analysis` sheet contains the fields of `CreditPosition`, except `position_id`. The loader derives `position_id` directly from `scenario_id`, so the workbook does not need a separate position identifier.

Examples:

| scenario_id | revenue | ebitda | revenue_growth |
|---|---:|---:|---:|
| TEST-001 | 1000000 | 100000 | 0.05 |

Numeric values use the same representation as the Python domain model. For example, a 5% growth rate is entered as `0.05`.

For rule `R009` (operating grants incidence), provide `operating_grants` and `production_value` in the same currency and accounting period. `production_value` means the total value of production from the source financial statements; it is not interchangeable with sales revenue. The rule evaluates `operating_grants / production_value` and is `NOT_EVALUABLE` if either input is missing, production value is non-positive, or grants are negative. A ratio above 10% triggers MEDIUM severity and above 20% triggers HIGH severity. These are configurable illustrative thresholds and should be calibrated for the sector and the bank's credit policy. Because operating grants may be recurring, the indicator flags reliance on them rather than automatically treating them as non-recurring income.

For rule `R010` (sustained increase in bank debt), provide `bank_debt_current`, `bank_debt_1y_ago`, `bank_debt_2y_ago`, `bank_debt_3y_ago`, and `bank_debt_4y_ago` in the same currency and on a consistent annual basis. The deterministic engine calculates current annual growth as `(bank_debt_current - bank_debt_1y_ago) / bank_debt_1y_ago`, then calculates the historical average from the three annual growth rates covering the prior three intervals. The indicator is the difference between current growth and historical average growth, in percentage points (represented as a decimal, e.g. `0.10` = 10 percentage points). A trigger requires both positive current-year debt growth and a difference above 10 percentage points; differences above 20 percentage points receive HIGH severity. These are illustrative thresholds that should be calibrated. The rule is `NOT_EVALUABLE` if any of the five debt levels is missing, non-numeric, negative, or if a denominator needed for the growth calculations is zero or negative.

For rule `R011` (increase in trade payables), provide `trade_payables_current`, `trade_payables_1y_ago`, `trade_payables_2y_ago`, `trade_payables_3y_ago`, and `trade_payables_4y_ago` in the same currency and on a consistent annual basis. The engine calculates current annual growth and compares it with the average growth over the prior three annual intervals, using the same method as R010. A trigger requires positive current-year growth and acceleration above 10 percentage points; acceleration above 20 percentage points receives HIGH severity. The rule is `NOT_EVALUABLE` when any input is missing, non-numeric, negative, or when a required prior-year denominator is zero or negative. These illustrative thresholds should be calibrated; an increase in trade payables alone does not prove payment stress and should be interpreted alongside revenue, purchasing activity and payment behaviour.

For rule `R012` (average payment days vs historical average), provide `avg_payment_days_current`, `avg_payment_days_1y_ago`, `avg_payment_days_2y_ago`, `avg_payment_days_3y_ago`, and `avg_payment_days_4y_ago`. Enter the average number of days on a consistent basis for each annual observation. The engine compares the current value with the arithmetic mean of the four prior annual values. The indicator is the difference in days, not percentages. A difference above 10 days triggers MEDIUM severity; a difference above 20 days triggers HIGH severity. The rule is `NOT_EVALUABLE` if an input is missing, non-numeric, non-finite, or negative. These thresholds are illustrative and should be calibrated to the company's sector, contractual payment terms and purchasing dynamics; an elevated payment-days level is a warning indicator, not by itself proof of financial distress.

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

The reference workbook keeps these inputs deliberately neutral across the three demonstration scenarios:

| scenario_id | average_utilization | overdraft_days | payment_delay_days | exposure_growth |
|---|---:|---:|---:|---:|
| DEMO-NORMAL | 0.50 | 2 | 5 | 0.05 |
| DEMO-ATTENTION | 0.50 | 2 | 5 | 0.05 |
| DEMO-CRITICAL | 0.50 | 2 | 5 | 0.05 |

This is intentional: the scenarios isolate differences in the financial assessment rather than introduce additional behavioural triggers.

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
