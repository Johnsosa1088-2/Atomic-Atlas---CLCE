from __future__ import annotations
from dataclasses import asdict
from copy import deepcopy
from typing import Any, Mapping
from .errors import ValidationError
from .validation import validate_contract
from .model import (
    Atlas, CandidateOverlay, Entity, Event, EvidenceReference, Observation,
    ProvenanceRecord, Region, Relation, Route,
)

SCHEMA = "ATLAS_DOCUMENT/0.1"


def _evidence(value: Mapping[str, Any] | None) -> EvidenceReference | None:
    if value is None:
        return None
    return EvidenceReference(**dict(value))


def atlas_to_dict(atlas: Atlas) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "version": atlas.version,
        "profile_id": atlas.profile_id,
        "state": deepcopy(atlas.state),
        "regions": [asdict(v) for v in atlas.regions.values()],
        "entities": [asdict(v) for v in atlas.entities.values()],
        "relations": [asdict(v) for v in atlas.relations],
        "routes": [asdict(v) for v in atlas.routes.values()],
        "candidate_overlays": [asdict(v) for v in atlas.candidate_overlays.values()],
        "events": [asdict(v) for v in atlas.events],
        "observations": [asdict(v) for v in atlas.observations],
        "provenance": [asdict(v) for v in atlas.provenance],
    }


def atlas_from_dict(data: Mapping[str, Any]) -> Atlas:
    if not isinstance(data, Mapping) or data.get("schema") != SCHEMA:
        raise ValidationError(f"document schema must be {SCHEMA}")
    validate_contract("document", dict(data))
    data = deepcopy(data)
    atlas = Atlas(version=data["version"], profile_id=data.get("profile_id"), state=dict(data.get("state", {})))
    for item in data.get("regions", []):
        atlas.add_region(Region(**item))
    for item in data.get("entities", []):
        atlas.add_entity(Entity(**item))
    for item in data.get("relations", []):
        atlas.add_relation(Relation(**item))
    for item in data.get("routes", []):
        atlas.add_route(Route(id=item["id"], entity_ids=tuple(item["entity_ids"]), purpose=item.get("purpose")))
    for item in data.get("candidate_overlays", []):
        entities = tuple(Entity(**x) for x in item.get("entities", []))
        relations = tuple(Relation(**x) for x in item.get("relations", []))
        routes = tuple(Route(id=x["id"], entity_ids=tuple(x["entity_ids"]), purpose=x.get("purpose")) for x in item.get("routes", []))
        atlas.add_candidate_overlay(CandidateOverlay(id=item["id"], entities=entities, relations=relations, routes=routes, status=item.get("status", "candidate")))
    for item in data.get("events", []):
        atlas.events.append(Event(sequence=item["sequence"], type=item["type"], payload=item.get("payload", {}), evidence=_evidence(item.get("evidence"))))
    if [e.sequence for e in atlas.events] != list(range(1, len(atlas.events)+1)):
        raise ValidationError("serialized events must form a contiguous sequence")
    for item in data.get("observations", []):
        atlas.record_observation(Observation(id=item["id"], payload=item.get("payload", {}), evidence=_evidence(item.get("evidence")), mutates_state=item.get("mutates_state", False)))
    atlas.provenance = [ProvenanceRecord(**x) for x in data.get("provenance", [])]
    atlas.validate_integrity()
    return atlas
