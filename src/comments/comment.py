from dataclasses import dataclass


@dataclass(frozen=True)
class Comment:
    rule_id: str
    text: str
