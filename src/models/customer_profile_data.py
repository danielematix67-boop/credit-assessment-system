from dataclasses import dataclass, field


@dataclass(frozen=True)
class CustomerProfileData:
    """Descriptive and risk-context inputs used in customer presentation."""

    company_name: str | None = None
    legal_form: str | None = None
    sector: str | None = None
    size_class: str | None = None
    geography: str | None = None
    shareholders: list[str] = field(default_factory=list)
    management_members: list[str] = field(default_factory=list)
    relationship_years: int | None = None
    business_history_years: int | None = None
    historical_facilities: list[str] = field(default_factory=list)
    active_ews: bool | None = None
    previous_restructuring: bool | None = None
