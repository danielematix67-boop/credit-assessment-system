from src.rules.registry import get_default_rules


EXPECTED_RULE_IDS = {
    "CP001",
    "CP002",
    "CP003",
    "R001",
    "R002",
    "R003",
    "R004",
    "R005",
    "R006",
    "R007",
    "B001",
    "B002",
    "B003",
    "B004",
    "DS001",
    "DS002",
    "DS003",
}


def test_default_rule_configuration_loads_all_rule_catalogs() -> None:
    rules = get_default_rules()
    rule_ids = {rule.config.rule_id for rule in rules}

    assert rule_ids == EXPECTED_RULE_IDS
    assert len(rules) == len(EXPECTED_RULE_IDS)
