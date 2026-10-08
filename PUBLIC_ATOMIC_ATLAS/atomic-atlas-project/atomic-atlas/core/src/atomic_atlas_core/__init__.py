"""Atomic Atlas neutral public core — behavior checkpoint.

No anatomy, physiology, physical transport solver, or domain-specific mechanism is
implemented here. The package provides neutral graph/state/provenance workflows.
"""
from .model import (
    Atlas, Entity, Relation, Route, Region, CandidateOverlay,
    StateSnapshot, Event, Observation, EvidenceReference,
    ProvenanceRecord, ReplayManifest,
)
from .analysis import TraceResult, trace_route, budget_preview
from .builder import build_atlas
from .serialization import atlas_to_dict, atlas_from_dict
from .runtime import AtlasRuntime, replay_declared_events
from .profiles import NeutralProfile, load_profile_dict
from .ledger import InMemoryAppendLedger, JsonlHashLedger
from .replay import RestartGuard, RestartStatus
from .provenance import sha256_bytes, sha256_json

__all__ = [
    "Atlas", "Entity", "Relation", "Route", "Region", "CandidateOverlay",
    "StateSnapshot", "Event", "Observation", "EvidenceReference",
    "ProvenanceRecord", "ReplayManifest", "TraceResult", "trace_route",
    "budget_preview", "build_atlas", "atlas_to_dict", "atlas_from_dict",
    "AtlasRuntime", "replay_declared_events", "NeutralProfile", "load_profile_dict",
    "InMemoryAppendLedger", "JsonlHashLedger", "RestartGuard", "RestartStatus",
    "sha256_bytes", "sha256_json",
]

from .validation import validate_contract
__all__.append("validate_contract")
