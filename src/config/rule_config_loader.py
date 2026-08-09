from pathlib import Path

import yaml

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity


class RuleConfigLoader:

    def load(self, path: Path) -> list[RuleConfig]:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        return [
            RuleConfig(
                rule_id=item["rule_id"],
                rule_name=item["rule_name"],
                category=item["category"],
                threshold=float(item["threshold"]),
                severity=RuleSeverity(item["severity"]),
            )
            for item in data["rules"]
        ]