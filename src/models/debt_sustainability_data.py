from dataclasses import dataclass


@dataclass(frozen=True)
class DebtSustainabilityData:
    """Deterministic inputs for debt-service and repayment-capacity analysis."""

    cash_flow_available_for_debt_service: float | None = None
    debt_service: float | None = None
    ebitda: float | None = None
    interest_expense: float | None = None
