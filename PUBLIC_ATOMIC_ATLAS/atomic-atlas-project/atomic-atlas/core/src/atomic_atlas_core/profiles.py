from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence
from .errors import ValidationError
from .validation import validate_contract
from .provenance import sha256_json

PROFILE_SCHEMA = "ATLAS_NEUTRAL_PROFILE/0.1"


def _ids(values: Sequence[str], name: str) -> tuple[str, ...]:
    out = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{name} entries must be nonempty strings")
        out.append(value.strip())
    if len(out) != len(set(out)):
        raise ValidationError(f"{name} entries must be unique")
    return tuple(out)


@dataclass(frozen=True)
class NeutralProfile:
    id: str
    possible: tuple[str, ...] = ()
    preferred: tuple[str, ...] = ()
    required: tuple[str, ...] = ()
    semantics: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValidationError("profile.id must be a nonempty string")
        object.__setattr__(self, "possible", _ids(self.possible, "possible"))
        object.__setattr__(self, "preferred", _ids(self.preferred, "preferred"))
        object.__setattr__(self, "required", _ids(self.required, "required"))
        # P10: categories are independent declarations. Core never promotes one into another.

    def digest(self) -> str:
        return sha256_json(self.as_dict())

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": PROFILE_SCHEMA,
            "id": self.id,
            "possible": list(self.possible),
            "preferred": list(self.preferred),
            "required": list(self.required),
            "semantics": dict(self.semantics),
        }


def load_profile_dict(data: Mapping[str, Any]) -> NeutralProfile:
    if not isinstance(data, Mapping) or data.get("schema") != PROFILE_SCHEMA:
        raise ValidationError(f"profile schema must be {PROFILE_SCHEMA}")
    validate_contract("neutral-profile", dict(data))
    return NeutralProfile(
        id=data["id"],
        possible=tuple(data.get("possible", [])),
        preferred=tuple(data.get("preferred", [])),
        required=tuple(data.get("required", [])),
        semantics=dict(data.get("semantics", {})),
    )
