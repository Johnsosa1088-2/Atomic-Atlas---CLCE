from __future__ import annotations
from dataclasses import dataclass, field, asdict
from copy import deepcopy
from typing import Any, Mapping, Sequence
from .errors import ValidationError
from .validation import validate_contract
from .provenance import sha256_json

UNKNOWN = None


def _nonempty(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} must be a nonempty string")
    return value.strip()


@dataclass(frozen=True)
class EvidenceReference:
    label: str
    digest: str | None = None
    verified: bool = False

    def __post_init__(self):
        _nonempty(self.label, "label")
        if self.digest is not None and (len(self.digest) != 64 or any(c not in "0123456789abcdef" for c in self.digest)):
            raise ValidationError("digest must be lowercase SHA-256 hex or null")


@dataclass(frozen=True)
class ProvenanceRecord:
    source_id: str
    version: str | None = None
    digest: str | None = None
    ancestor_id: str | None = None
    transform: str | None = None

    def __post_init__(self):
        _nonempty(self.source_id, "source_id")


@dataclass(frozen=True)
class Region:
    id: str
    bounds: Mapping[str, Any] | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        _nonempty(self.id, "region.id")


@dataclass(frozen=True)
class Entity:
    id: str
    type: str | None = None
    region_id: str | None = None
    coordinates: Mapping[str, float | None] | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)
    candidate: bool = False

    def __post_init__(self):
        _nonempty(self.id, "entity.id")


@dataclass(frozen=True)
class Relation:
    source: str
    target: str
    type: str
    directed: bool = False
    reversible: bool | None = None
    transport_enabled: bool = False
    state_mutation_enabled: bool = False
    attributes: Mapping[str, Any] = field(default_factory=dict)
    candidate: bool = False

    def __post_init__(self):
        _nonempty(self.source, "relation.source")
        _nonempty(self.target, "relation.target")
        _nonempty(self.type, "relation.type")


@dataclass(frozen=True)
class Route:
    id: str
    entity_ids: tuple[str, ...]
    purpose: str | None = None

    def __post_init__(self):
        _nonempty(self.id, "route.id")
        if len(self.entity_ids) < 1:
            raise ValidationError("route must contain at least one entity")


@dataclass(frozen=True)
class CandidateOverlay:
    id: str
    entities: tuple[Entity, ...] = ()
    relations: tuple[Relation, ...] = ()
    routes: tuple[Route, ...] = ()
    status: str = "candidate"

    def __post_init__(self):
        _nonempty(self.id, "candidate_overlay.id")
        if self.status != "candidate":
            raise ValidationError("candidate overlay status must remain 'candidate' in core")
        if any(not e.candidate for e in self.entities):
            raise ValidationError("candidate overlay entities must be marked candidate=True")
        if any(not r.candidate for r in self.relations):
            raise ValidationError("candidate overlay relations must be marked candidate=True")
        if any(r.transport_enabled or r.state_mutation_enabled for r in self.relations):
            raise ValidationError("candidate relations cannot enable transport or state mutation in neutral core")


@dataclass(frozen=True)
class Event:
    sequence: int
    type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    evidence: EvidenceReference | None = None

    def __post_init__(self):
        if type(self.sequence) is not int or self.sequence < 1:
            raise ValidationError("event.sequence must be a positive integer")
        _nonempty(self.type, "event.type")


@dataclass(frozen=True)
class Observation:
    id: str
    payload: Mapping[str, Any]
    evidence: EvidenceReference
    mutates_state: bool = False

    def __post_init__(self):
        _nonempty(self.id, "observation.id")
        if self.mutates_state:
            raise ValidationError("observations cannot mutate state in neutral core")


@dataclass(frozen=True)
class StateSnapshot:
    schema: str
    state: Mapping[str, Any]
    event_count: int
    source_digest: str | None = None
    topology_digest: str | None = None
    restart_status: str = "FRESH"

    def __post_init__(self):
        _nonempty(self.schema, "state_snapshot.schema")
        if type(self.event_count) is not int or self.event_count < 0:
            raise ValidationError("event_count must be a nonnegative integer")

    def digest(self) -> str:
        return sha256_json(asdict(self))


@dataclass(frozen=True)
class ReplayManifest:
    scope: str
    inputs: Mapping[str, Any]
    source_digest: str | None = None
    topology_digest: str | None = None
    state_digest: str | None = None
    full_dynamic_replay: bool = False

    def __post_init__(self):
        _nonempty(self.scope, "replay_manifest.scope")
        if self.full_dynamic_replay and self.scope != "FULL_DYNAMIC_REPLAY":
            raise ValidationError("full_dynamic_replay requires explicit FULL_DYNAMIC_REPLAY scope")


@dataclass
class Atlas:
    version: str
    regions: dict[str, Region] = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)
    relations: list[Relation] = field(default_factory=list)
    routes: dict[str, Route] = field(default_factory=dict)
    candidate_overlays: dict[str, CandidateOverlay] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    profile_id: str | None = None
    provenance: list[ProvenanceRecord] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        _nonempty(self.version, "atlas.version")
        validate_contract("build-spec", {"schema":"ATLAS_BUILD_SPEC/0.1","version":self.version,"initial_state":self.state})
        self.state = deepcopy(self.state)

    def add_region(self, region: Region) -> None:
        if region.id in self.regions:
            raise ValidationError(f"duplicate region id: {region.id}")
        self.regions[region.id] = region

    def add_entity(self, entity: Entity) -> None:
        validate_contract("entity", asdict(entity))
        if entity.candidate:
            raise ValidationError("candidate entities must be added through a candidate overlay")
        if entity.id in self.entities:
            raise ValidationError(f"duplicate entity id: {entity.id}")
        if entity.region_id is not None and entity.region_id not in self.regions:
            raise ValidationError(f"unknown region id: {entity.region_id}")
        self.entities[entity.id] = entity

    def add_relation(self, relation: Relation) -> None:
        validate_contract("relation", asdict(relation))
        if relation.candidate:
            raise ValidationError("candidate relations must be added through a candidate overlay")
        if relation.source not in self.entities or relation.target not in self.entities:
            raise ValidationError("relation endpoints must exist in established entities")
        self.relations.append(relation)

    def add_route(self, route: Route) -> None:
        missing = [x for x in route.entity_ids if x not in self.entities]
        if missing:
            raise ValidationError(f"route references unknown established entities: {missing}")
        if route.id in self.routes:
            raise ValidationError(f"duplicate route id: {route.id}")
        self.routes[route.id] = route

    def add_candidate_overlay(self, overlay: CandidateOverlay) -> None:
        validate_contract("candidate-overlay", asdict(overlay))
        if overlay.id in self.candidate_overlays:
            raise ValidationError(f"duplicate candidate overlay id: {overlay.id}")
        candidate_ids = [e.id for e in overlay.entities]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValidationError("candidate entity ids must be unique within an overlay")
        if set(candidate_ids) & set(self.entities):
            raise ValidationError("candidate entity ids cannot shadow established ids")
        allowed = set(self.entities) | set(candidate_ids)
        for e in overlay.entities:
            if e.region_id is not None and e.region_id not in self.regions:
                raise ValidationError("candidate entity references unknown established region")
        for relation in overlay.relations:
            if relation.source not in allowed or relation.target not in allowed:
                raise ValidationError("candidate relation endpoints must exist in established or same-overlay entities")
        route_ids = [route.id for route in overlay.routes]
        if len(route_ids) != len(set(route_ids)):
            raise ValidationError("candidate route ids must be unique within an overlay")
        for route in overlay.routes:
            if any(ident not in allowed for ident in route.entity_ids):
                raise ValidationError("candidate route references unknown entity")
        self.candidate_overlays[overlay.id] = deepcopy(overlay)

    def record_observation(self, observation: Observation) -> None:
        validate_contract("observation", asdict(observation))
        self.observations.append(deepcopy(observation))

    def apply_event(self, event: Event) -> None:
        validate_contract("event", asdict(event))
        event = deepcopy(event)
        expected = len(self.events) + 1
        if event.sequence != expected:
            raise ValidationError(f"event sequence must be {expected}")
        patch = event.payload.get("state_patch") if isinstance(event.payload, Mapping) else None
        if patch is not None:
            if not isinstance(patch, Mapping):
                raise ValidationError("state_patch must be a mapping")
            set_values = patch.get("set", {})
            delete_keys = patch.get("delete", [])
            if not isinstance(set_values, Mapping) or not isinstance(delete_keys, Sequence) or isinstance(delete_keys, (str, bytes)):
                raise ValidationError("state_patch requires mapping set and sequence delete")
            for key in delete_keys:
                if not isinstance(key, str) or not key:
                    raise ValidationError("state_patch delete keys must be nonempty strings")
            if any(not isinstance(key, str) or not key for key in set_values):
                raise ValidationError("state_patch set keys must be nonempty strings")
            self.state.update(deepcopy(dict(set_values)))
            for key in delete_keys:
                self.state.pop(key, None)
        self.events.append(deepcopy(event))

    def validate_integrity(self) -> None:
        validate_contract("topology", self.topology_payload())
        if any(key != region.id for key, region in self.regions.items()):
            raise ValidationError("region dictionary keys must equal region ids")
        if any(key != entity.id for key, entity in self.entities.items()):
            raise ValidationError("entity dictionary keys must equal entity ids")
        for e in self.entities.values():
            if e.region_id is not None and e.region_id not in self.regions:
                raise ValidationError(f"unknown region id: {e.region_id}")
        for r in self.relations:
            if r.source not in self.entities or r.target not in self.entities:
                raise ValidationError("established relation endpoint missing")
        if any(key != route.id for key, route in self.routes.items()):
            raise ValidationError("route dictionary keys must equal route ids")
        if any(key != overlay.id for key, overlay in self.candidate_overlays.items()):
            raise ValidationError("candidate overlay dictionary keys must equal overlay ids")
        for route in self.routes.values():
            if any(x not in self.entities for x in route.entity_ids):
                raise ValidationError(f"route {route.id} references unknown entity")
        check = Atlas(self.version, regions=dict(self.regions), entities=dict(self.entities))
        for overlay in self.candidate_overlays.values():
            check.add_candidate_overlay(overlay)
        if [e.sequence for e in self.events] != list(range(1, len(self.events)+1)):
            raise ValidationError("events must form a contiguous sequence")

    def topology_payload(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "regions": {k: asdict(v) for k, v in self.regions.items()},
            "entities": {k: asdict(v) for k, v in self.entities.items()},
            "relations": [asdict(v) for v in self.relations],
            "routes": {k: asdict(v) for k, v in self.routes.items()},
        }

    def topology_digest(self) -> str:
        return sha256_json(self.topology_payload())

    def state_digest(self) -> str:
        return sha256_json({"state": self.state, "event_count": len(self.events)})

    def source_digest(self) -> str:
        return sha256_json({"version": self.version, "provenance": [asdict(v) for v in self.provenance]})

    def snapshot(self, *, schema: str = "ATLAS_STATE/0.1", restart_status: str = "FRESH") -> StateSnapshot:
        established = {
            "version": self.version,
            "profile_id": self.profile_id,
            "runtime_state": deepcopy(self.state),
            "regions": {k: asdict(v) for k, v in self.regions.items()},
            "entities": {k: asdict(v) for k, v in self.entities.items()},
            "relations": [asdict(v) for v in self.relations],
            "routes": {k: asdict(v) for k, v in self.routes.items()},
        }
        snapshot = StateSnapshot(schema=schema, state=established, event_count=len(self.events), source_digest=self.source_digest(), topology_digest=self.topology_digest(), restart_status=restart_status)
        validate_contract("state-snapshot", asdict(snapshot))
        return snapshot
