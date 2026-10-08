from __future__ import annotations
from typing import Any, Mapping
from .errors import ValidationError
from .validation import validate_contract
from .model import Atlas, Entity, Region, Relation, Route, ProvenanceRecord

BUILD_SCHEMA = "ATLAS_BUILD_SPEC/0.1"


def build_atlas(spec: Mapping[str, Any]) -> Atlas:
    if not isinstance(spec, Mapping) or spec.get("schema") != BUILD_SCHEMA:
        raise ValidationError(f"build spec schema must be {BUILD_SCHEMA}")
    validate_contract("build-spec", dict(spec))
    atlas = Atlas(version=spec["version"], profile_id=spec.get("profile_id"), state=dict(spec.get("initial_state", {})))
    for item in spec.get("regions", []):
        atlas.add_region(Region(**item))
    for item in spec.get("entities", []):
        atlas.add_entity(Entity(**item))
    for item in spec.get("relations", []):
        atlas.add_relation(Relation(**item))
    for item in spec.get("routes", []):
        atlas.add_route(Route(id=item["id"], entity_ids=tuple(item["entity_ids"]), purpose=item.get("purpose")))
    atlas.provenance = [ProvenanceRecord(**x) for x in spec.get("provenance", [])]
    atlas.validate_integrity()
    return atlas
