from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from .errors import ValidationError


@dataclass(frozen=True)
class InterpretationView:
    aliases: Mapping[str, str]

    def __post_init__(self):
        if len(set(self.aliases.values())) != len(self.aliases):
            raise ValidationError("interpretation aliases must be one-to-one")

    def project(self, identifiers: list[str]) -> list[dict[str, str]]:
        return [{"source_id": i, "alias": self.aliases[i]} for i in identifiers]
