from dataclasses import dataclass, field

from src.models.ews_score import EwsScoreClass


# Regulatory risk-grade vocabulary used by the Customer Profile context.
REGULATORY_RISK_GRADES = ("Bonis", "Past Due", "Unlikely to Pay", "Bad Loan")


@dataclass(frozen=True)
class CustomerProfileData:
    """Descriptive, risk-context and relevant-event inputs for customer presentation."""

    # General information
    company_name: str | None = None
    counterparty_type: str | None = None
    legal_form: str | None = None
    sector: str | None = None
    size_class: str | None = None
    geography: str | None = None
    business_history_years: int | None = None
    operations: list[str] = field(default_factory=list)

    # Risk-grade evolution
    forborne_non_performing_exit: bool | None = None
    past_due_count: int | None = None
    cure_period_days: int | None = None
    monitoring_period_days: int | None = None
    probation_period_days: int | None = None
    minimum_regulatory_risk_grade: str | None = None
    previous_risk_grade: str | None = None
    risk_grade_change: str | None = None

    # Statistical predictiveness
    ews_score_class: EwsScoreClass | None = None
    ews_score_notching: str | None = None
    ews_score_variation: float | None = None
    active_ewis: list[str] = field(default_factory=list)
    rating: str | None = None
    rating_notching: str | None = None
    rating_influential_factors: list[str] = field(default_factory=list)
    rating_elementary_modules: list[str] = field(default_factory=list)
    pd: float | None = None

    # Risk group
    risk_group_interdependence: str | None = None
    risk_group_independence: str | None = None

    # Ownership / management / counterparty-specific information
    shareholders: list[str] = field(default_factory=list)
    shareholder_roles: list[str] = field(default_factory=list)
    management_members: list[str] = field(default_factory=list)
    generational_transition: bool | None = None
    employment_contract_type: str | None = None
    economic_family_context: str | None = None

    # Banking relationship / credit history
    relationship_years: int | None = None
    historical_facilities: list[str] = field(default_factory=list)
    previous_restructuring: bool | None = None
    forborne: bool | None = None

    # Relevant events
    protests: list[str] = field(default_factory=list)
    bankruptcies: list[str] = field(default_factory=list)
    litigation: list[str] = field(default_factory=list)
    significant_historical_events: list[str] = field(default_factory=list)
