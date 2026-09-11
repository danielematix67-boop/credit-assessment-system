from pathlib import Path

import yaml

from src.rules.base.config import RuleConfig
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection
from src.rules.base.severity_threshold import SeverityThreshold


class RuleConfigLoader:
    """Load and validate rule definitions from YAML configuration."""

    _VALID_TRIGGER_OPERATORS = {"GT", "GTE", "LT", "LTE"}
    _VALID_CALCULATIONS = {"direct", "ratio", "difference"}

    def load(self, path: Path) -> list[RuleConfig]:
        """Load rules from a YAML file or all rule catalogs in a directory."""
        paths = sorted(path.glob("*_rules.yaml")) if path.is_dir() else [path]
        if not paths:
            raise ValueError(f"No rule configuration files found in: {path}")

        rules: list[dict] = []
        for config_path in paths:
            with config_path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file)

            if not isinstance(data, dict):
                raise ValueError("Invalid rule configuration")
            if "rules" not in data:
                raise ValueError("Missing 'rules' section")
            file_rules = data["rules"]
            if not isinstance(file_rules, list):
                raise ValueError("'rules' must be a list")
            rules.extend(file_rules)

        return self._build_configs(rules)

    def _build_configs(self, rules: list[dict]) -> list[RuleConfig]:
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
                "severity_direction",
            }
            missing_fields = required_fields - item.keys()
            if missing_fields:
                raise ValueError(
                    f"Missing required fields: {sorted(missing_fields)}",
                )

            rule_id = item["rule_id"]
            if rule_id in seen_rule_ids:
                raise ValueError(f"Duplicate rule_id: {rule_id}")
            seen_rule_ids.add(rule_id)

            try:
                threshold = float(item["threshold"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid threshold for rule_id: {rule_id}") from exc
            try:
                severity = RuleSeverity(item["severity"])
            except ValueError as exc:
                raise ValueError(f"Invalid severity for rule_id: {rule_id}") from exc
            try:
                severity_direction = SeverityDirection(item["severity_direction"])
            except ValueError as exc:
                raise ValueError(
                    f"Invalid severity direction for rule_id: {rule_id}",
                ) from exc

            indicator = item.get("indicator", item["rule_name"])
            if not isinstance(indicator, str) or not indicator.strip():
                raise ValueError(f"Invalid indicator for rule_id: {rule_id}")

            input_field = item.get("input_field", "")
            if not isinstance(input_field, str):
                raise ValueError(f"Invalid input_field for rule_id: {rule_id}")

            raw_input_fields = item.get("input_fields", [])
            if not isinstance(raw_input_fields, list) or not all(
                isinstance(field, str) and field.strip()
                for field in raw_input_fields
            ):
                raise ValueError(f"Invalid input_fields for rule_id: {rule_id}")

            calculation = item.get("calculation", "direct")
            if not isinstance(calculation, str):
                raise ValueError(f"Invalid calculation for rule_id: {rule_id}")
            calculation = calculation.strip().lower()
            if calculation not in self._VALID_CALCULATIONS:
                raise ValueError(
                    f"Invalid calculation for rule_id: {rule_id}: {calculation}",
                )

            comment_template = item.get("comment_template", "")
            if not isinstance(comment_template, str):
                raise ValueError(f"Invalid comment_template for rule_id: {rule_id}")

            trigger_operator = item.get("trigger_operator", "GT")
            if not isinstance(trigger_operator, str):
                raise ValueError(f"Invalid trigger_operator for rule_id: {rule_id}")
            trigger_operator = trigger_operator.strip().upper()
            if trigger_operator not in self._VALID_TRIGGER_OPERATORS:
                raise ValueError(
                    "Invalid trigger_operator for rule_id: "
                    f"{rule_id}: {trigger_operator}",
                )

            severity_thresholds: list[SeverityThreshold] = []
            raw_severity_thresholds = item.get("severity_thresholds", [])
            if not isinstance(raw_severity_thresholds, list):
                raise ValueError(
                    f"Invalid severity_thresholds for rule_id: {rule_id}",
                )
            for severity_threshold in raw_severity_thresholds:
                if not isinstance(severity_threshold, dict):
                    raise ValueError(
                        "Invalid severity threshold configuration for "
                        f"rule_id: {rule_id}",
                    )
                required_severity_fields = {"threshold", "severity"}
                missing_severity_fields = (
                    required_severity_fields - severity_threshold.keys()
                )
                if missing_severity_fields:
                    raise ValueError(
                        "Missing severity threshold fields for rule_id: "
                        f"{rule_id}: {sorted(missing_severity_fields)}",
                    )
                try:
                    severity_value = float(severity_threshold["threshold"])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Invalid severity threshold for rule_id: {rule_id}",
                    ) from exc
                try:
                    severity_level = RuleSeverity(
                        severity_threshold["severity"],
                    )
                except ValueError as exc:
                    raise ValueError(
                        "Invalid severity for severity threshold of rule_id: "
                        f"{rule_id}",
                    ) from exc
                severity_thresholds.append(
                    SeverityThreshold(
                        threshold=severity_value,
                        severity=severity_level,
                    ),
                )

            configs.append(
                RuleConfig(
                    rule_id=rule_id,
                    rule_name=item["rule_name"],
                    category=item["category"],
                    threshold=threshold,
                    severity=severity,
                    severity_direction=severity_direction,
                    severity_thresholds=tuple(severity_thresholds),
                    indicator=indicator.strip(),
                    input_field=input_field.strip(),
                    input_fields=tuple(
                        field.strip() for field in raw_input_fields
                    ),
                    calculation=calculation,
                    comment_template=comment_template.strip(),
                    trigger_operator=trigger_operator,
                ),
            )
        return configs
