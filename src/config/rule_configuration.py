from pathlib import Path


class RuleConfiguration:
    def __init__(self, rules_path: Path):
        self.rules_path = rules_path

    @classmethod
    def default(cls) -> "RuleConfiguration":
        """Return the default configuration for the core Rule Engine catalog."""
        return cls(Path("config/financial_analysis_rules.yaml"))
