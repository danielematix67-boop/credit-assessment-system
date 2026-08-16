from pathlib import Path

import yaml

from src.rules.base.config import RuleConfig, SeverityThreshold
from src.rules.base.severity import RuleSeverity
from src.rules.base.severity_direction import SeverityDirection


class RuleConfigLoader:

    def load(
        self,
        path: Path,
    ) -> list[RuleConfig]:

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = yaml.safe_load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "Invalid rule configuration"
            )

        if "rules" not in data:
            raise ValueError(
                "Missing 'rules' section"
            )

        rules = data["rules"]

        if not isinstance(rules, list):
            raise ValueError(
                "'rules' must be a list"
            )

        configs = []

        seen_rule_ids = set()

        for item in rules:

            if not isinstance(item, dict):
                raise ValueError(
                    "Invalid rule configuration item"
                )

            required_fields = {
                "rule_id",
                "rule_name",
                "category",
                "threshold",
                "severity",
                "severity_direction",
            }

            missing_fields = (
                required_fields - item.keys()
            )

            if missing_fields:
                raise ValueError(
                    "Missing required fields: "
                    f"{sorted(missing_fields)}"
                )

            rule_id = item["rule_id"]

            if rule_id in seen_rule_ids:
                raise ValueError(
                    f"Duplicate rule_id: {rule_id}"
                )

            seen_rule_ids.add(rule_id)

            # ==================================================
            # Main rule threshold
            # ==================================================

            try:
                threshold = float(
                    item["threshold"]
                )

            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid threshold for rule_id: {rule_id}"
                ) from exc

            # ==================================================
            # Default severity
            # ==================================================

            try:
                severity = RuleSeverity(
                    item["severity"]
                )

            except ValueError as exc:
                raise ValueError(
                    f"Invalid severity for rule_id: {rule_id}"
                ) from exc

            # ==================================================
            # Severity direction
            # ==================================================

            try:
                severity_direction = SeverityDirection(
                    item["severity_direction"]
                )

            except ValueError as exc:
                raise ValueError(
                    "Invalid severity direction for "
                    f"rule_id: {rule_id}"
                ) from exc

            # ==================================================
            # Severity thresholds
            # ==================================================

            severity_thresholds = []

            raw_severity_thresholds = item.get(
                "severity_thresholds",
                [],
            )

            if not isinstance(
                raw_severity_thresholds,
                list,
            ):
                raise ValueError(
                    "Invalid severity_thresholds for "
                    f"rule_id: {rule_id}"
                )

            for severity_threshold in (
                raw_severity_thresholds
            ):

                if not isinstance(
                    severity_threshold,
                    dict,
                ):
                    raise ValueError(
                        "Invalid severity threshold "
                        f"configuration for rule_id: {rule_id}"
                    )

                required_severity_fields = {
                    "threshold",
                    "severity",
                }

                missing_severity_fields = (
                    required_severity_fields
                    - severity_threshold.keys()
                )

                if missing_severity_fields:
                    raise ValueError(
                        "Missing severity threshold fields "
                        f"for rule_id: {rule_id}: "
                        f"{sorted(missing_severity_fields)}"
                    )

                try:
                    severity_value = float(
                        severity_threshold["threshold"]
                    )

                except (
                    TypeError,
                    ValueError,
                ) as exc:
                    raise ValueError(
                        "Invalid severity threshold for "
                        f"rule_id: {rule_id}"
                    ) from exc

                try:
                    severity_level = RuleSeverity(
                        severity_threshold["severity"]
                    )

                except ValueError as exc:
                    raise ValueError(
                        "Invalid severity for severity threshold "
                        f"of rule_id: {rule_id}"
                    ) from exc

                severity_thresholds.append(
                    SeverityThreshold(
                        threshold=severity_value,
                        severity=severity_level,
                    )
                )

            # ==================================================
            # Build RuleConfig
            # ==================================================

            configs.append(
                RuleConfig(
                    rule_id=rule_id,
                    rule_name=item["rule_name"],
                    category=item["category"],
                    threshold=threshold,
                    severity=severity,
                    severity_direction=severity_direction,
                    severity_thresholds=tuple(
                        severity_thresholds
                    ),
                )
            )

        return configs
