from __future__ import annotations
from dataclasses import asdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping
from .builder import build_atlas
from .errors import ValidationError
from .validation import validate_contract
from .ledger import JsonlHashLedger
from .model import Atlas, CandidateOverlay, Event, Observation, ReplayManifest
from .profiles import NeutralProfile
from .provenance import sha256_json
from .replay import RestartGuard, RestartStatus
from .serialization import atlas_from_dict, atlas_to_dict
from .strict_json import loads_strict_json


class AtlasRuntime:
    """Coordinated neutral workflow. No domain physics is implemented here."""

    def __init__(self, atlas: Atlas, *, profile: NeutralProfile | None = None, ledger: JsonlHashLedger | None = None):
        self.atlas = atlas
        self.profile = profile
        self.ledger = ledger
        self._restart_guard = None
        if profile is not None:
            self.attach_profile(profile)

    def attach_profile(self, profile: NeutralProfile) -> None:
        if self.atlas.profile_id not in (None, profile.id):
            raise ValidationError("atlas already names a different profile")
        self.profile = profile
        self.atlas.profile_id = profile.id

    def _commit(self, staged: Atlas, record_type: str, payload: Mapping[str, Any]) -> str | None:
        # Publish only after the ledger accepts the staged transition. Keep Atlas identity.
        head = self._append_ledger(record_type, payload)
        self.atlas.__dict__.update(staged.__dict__)
        return head

    def attach_candidate_overlay(self, overlay: CandidateOverlay) -> str | None:
        staged = deepcopy(self.atlas)
        staged.add_candidate_overlay(overlay)
        return self._commit(staged, "candidate_overlay_attached", {"overlay": asdict(overlay)})

    def record_observation(self, observation: Observation) -> str | None:
        staged = deepcopy(self.atlas)
        before = staged.state_digest()
        staged.record_observation(observation)
        if staged.state_digest() != before:
            raise RuntimeError("observation mutated established state")
        return self._commit(staged, "observation_recorded", {"observation": asdict(observation)})

    def apply_state_event(self, *, event_type: str, set_values: Mapping[str, Any] | None = None,
                          delete_keys: tuple[str, ...] = (), evidence=None) -> Event:
        sequence = len(self.atlas.events) + 1
        patch = {"set": deepcopy(dict(set_values or {})), "delete": list(delete_keys)}
        event = Event(sequence=sequence, type=event_type, payload={"state_patch": patch}, evidence=deepcopy(evidence))
        staged = deepcopy(self.atlas)
        staged.apply_event(event)
        self._commit(staged, "state_event_applied", {"event": asdict(event), "state_digest": staged.state_digest()})
        return deepcopy(event)

    def document(self) -> dict[str, Any]:
        return atlas_to_dict(self.atlas)

    def save(self, path: str | Path, *, guard: RestartGuard | None = None) -> Path:
        if self._restart_guard is not None:
            self._restart_guard.ensure_writable()
        guard = guard if guard is not None else self._restart_guard
        if guard is not None:
            guard.ensure_writable()
            if guard.status != RestartStatus.RESET_AFTER_BLOCKED_RESTART:
                guard.check(source_digest=self.atlas.source_digest(), topology_digest=self.atlas.topology_digest(), state_digest=self.atlas.state_digest())
            guard.ensure_writable()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        import json
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(self.document(), indent=2, sort_keys=True), encoding="utf-8")
        temp.replace(path)
        return path

    @classmethod
    def load(cls, path: str | Path, *, profile: NeutralProfile | None = None, ledger: JsonlHashLedger | None = None,
             guard: RestartGuard | None = None) -> "AtlasRuntime":
        import json
        data = loads_strict_json(Path(path).read_bytes())
        atlas = atlas_from_dict(data)
        if guard is not None:
            status = guard.check(source_digest=atlas.source_digest(), topology_digest=atlas.topology_digest(), state_digest=atlas.state_digest())
            guard.ensure_writable() if not status.value.startswith("BLOCKED_") else None
        runtime = cls(atlas, profile=profile, ledger=ledger)
        runtime._restart_guard = guard
        return runtime

    def replay_manifest(self, scope: str = "DECLARED_EVENT_REPLAY") -> ReplayManifest:
        manifest = ReplayManifest(
            scope=scope,
            inputs={
                "version": self.atlas.version,
                "profile_id": self.atlas.profile_id,
                "profile_digest": self.profile.digest() if self.profile else None,
                "event_count": len(self.atlas.events),
            },
            source_digest=self.atlas.source_digest(),
            topology_digest=self.atlas.topology_digest(),
            state_digest=self.atlas.state_digest(),
            full_dynamic_replay=False,
        )
        validate_contract("replay-manifest", asdict(manifest))
        return manifest

    def _append_ledger(self, record_type: str, payload: Mapping[str, Any]) -> str | None:
        if self.ledger is None:
            return None
        return self.ledger.append({"type": record_type, "payload": dict(payload)})


def replay_declared_events(baseline: Atlas, events: list[Event]) -> Atlas:
    """Reapply only neutral state_patch events to a baseline copy via serialization."""
    if baseline.events:
        raise ValidationError("declared-event replay requires an event-free baseline")
    baseline.validate_integrity()
    clone = atlas_from_dict(atlas_to_dict(baseline))
    for event in events:
        clone.apply_event(event)
    return clone
