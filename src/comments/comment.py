from dataclasses import dataclass


@dataclass
class Comment:
    rule_id: str
    text: str