from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerProfileAnalysis:
    """Structured contextual customer-profile information for reporting."""

    general_information: str = ""
    risk_profile: str = ""
    relationship_context: str = ""
    relevant_events: str = ""

    def sections(self) -> list[tuple[str, str]]:
        """Return populated profile sections in authoritative reporting order."""
        return [
            ("General Information", self.general_information),
            ("Risk Profile & Predictiveness", self.risk_profile),
            ("Relationship & Counterparty Context", self.relationship_context),
            ("Relevant Events", self.relevant_events),
        ]
