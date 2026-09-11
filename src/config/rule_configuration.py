from pathlib import Path


class RuleConfiguration:
    def __init__(self, rules_path: Path):
        self.rules_path = rules_path

    @classmethod
    def default(cls) -> "RuleConfiguration":
        return cls(Path("config/financial_analysis_rules.yaml"))
