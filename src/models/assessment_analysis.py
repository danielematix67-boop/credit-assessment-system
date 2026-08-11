from dataclasses import dataclass


@dataclass
class AssessmentAnalysis:
    position_id: str
    key_findings: list[str]
    risk_factors: list[str]
    limitations: list[str]