from pathlib import Path

import yaml

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity


class RuleConfigLoader:

    def load(self, path: Path) -> list[RuleConfig]:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if not isinstance(data, dict):
            raise ValueError("Invalid rule configuration")

        if "rules" not in data:
            raise ValueError("Missing 'rules' section")

        rules = data["rules"]

        if not isinstance(rules, list):
            raise ValueError("'rules' must be a list")

        configs = []

        seen_rule_ids = set()

        for item in rules:
            if not isinstance(item, dict):
                raise ValueError("Invalid rule configuration item")

            required_fields = {
                "rule_id",
                "rule_name",
                "category",
                "threshold",
                "severity",
            }

            missing_fields = required_fields - item.keys()

            if missing_fields:
                raise ValueError(
                    f"Missing required fields: {sorted(missing_fields)}"
                )

            rule_id = item["rule_id"]

            if rule_id in seen_rule_ids:
                raise ValueError(
                    f"Duplicate rule_id: {rule_id}"
                )

            seen_rule_ids.add(rule_id)

            try:
                threshold = float(item["threshold"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid threshold for rule_id: {rule_id}"
                ) from exc

            try:
                severity = RuleSeverity(item["severity"])
            except ValueError as exc:
                raise ValueError(
                    f"Invalid severity for rule_id: {rule_id}"
                ) from exc

            configs.append(
                RuleConfig(
                    rule_id=rule_id,
                    rule_name=item["rule_name"],
                    category=item["category"],
                    threshold=threshold,
                    severity=severity,
                )
            )

        return configs
