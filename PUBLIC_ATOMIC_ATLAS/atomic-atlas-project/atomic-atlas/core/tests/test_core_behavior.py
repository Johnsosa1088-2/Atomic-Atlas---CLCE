import json
from pathlib import Path
import pytest
from atomic_atlas_core import (
    Atlas, AtlasRuntime, CandidateOverlay, Entity, EvidenceReference, JsonlHashLedger,
    NeutralProfile, Observation, Relation, Region, RestartGuard, RestartStatus,
    atlas_from_dict, atlas_to_dict, build_atlas, replay_declared_events,
)
from atomic_atlas_core.errors import RestartBlockedError, ValidationError


def make_atlas():
    a = Atlas("v", state={"mode": "idle"})
    a.add_region(Region("r"))
    a.add_entity(Entity("a", region_id="r"))
    a.add_entity(Entity("b", region_id="r"))
    a.add_relation(Relation("a", "b", "declared_connection"))
    return a


def test_build_validate_and_roundtrip():
    spec = {"schema":"ATLAS_BUILD_SPEC/0.1","version":"v","regions":[{"id":"r"}],"entities":[{"id":"a","region_id":"r"}],"initial_state":{"x":1}}
    atlas = build_atlas(spec)
    again = atlas_from_dict(atlas_to_dict(atlas))
    assert again.state == {"x": 1}
    assert again.topology_digest() == atlas.topology_digest()


def test_explicit_event_is_only_runtime_state_mutator():
    runtime = AtlasRuntime(make_atlas())
    before = runtime.atlas.state_digest()
    runtime.record_observation(Observation("o", {"x": 1}, EvidenceReference("fixture")))
    assert runtime.atlas.state_digest() == before
    runtime.apply_state_event(event_type="change", set_values={"mode":"active"})
    assert runtime.atlas.state["mode"] == "active"


def test_candidate_overlay_does_not_change_state_digest():
    runtime = AtlasRuntime(make_atlas())
    before = runtime.atlas.state_digest()
    overlay = CandidateOverlay("c", entities=(Entity("c:a", candidate=True),))
    runtime.attach_candidate_overlay(overlay)
    assert runtime.atlas.state_digest() == before


def test_profile_categories_are_independent_p10():
    p = NeutralProfile("p", possible=("a",), preferred=("b",), required=("c",))
    assert p.possible == ("a",) and p.preferred == ("b",) and p.required == ("c",)


def test_jsonl_ledger_detects_tampering(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = JsonlHashLedger(path)
    ledger.append({"a": 1})
    ledger.append({"b": 2})
    assert JsonlHashLedger(path).count == 2
    lines = path.read_text().splitlines()
    item = json.loads(lines[0]); item["record"]["a"] = 9
    lines[0] = json.dumps(item, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValidationError):
        JsonlHashLedger(path)


def test_save_is_blocked_on_mismatched_lineage(tmp_path):
    runtime = AtlasRuntime(make_atlas())
    guard = RestartGuard(expected_source_digest="not-this")
    guard.check(source_digest=runtime.atlas.source_digest(), topology_digest=runtime.atlas.topology_digest(), state_digest=runtime.atlas.state_digest())
    with pytest.raises(RestartBlockedError):
        runtime.save(tmp_path / "atlas.json", guard=guard)


def test_declared_event_replay_reproduces_runtime_state():
    baseline = make_atlas()
    runtime = AtlasRuntime(atlas_from_dict(atlas_to_dict(baseline)))
    runtime.apply_state_event(event_type="change", set_values={"mode":"active", "n":1})
    runtime.apply_state_event(event_type="increment-declared", set_values={"n":2})
    replayed = replay_declared_events(baseline, runtime.atlas.events)
    assert replayed.state == runtime.atlas.state
    assert replayed.state_digest() == runtime.atlas.state_digest()


def test_serialized_event_sequence_gap_is_rejected():
    a = make_atlas()
    runtime = AtlasRuntime(a)
    runtime.apply_state_event(event_type="x", set_values={"x":1})
    doc = atlas_to_dict(a)
    doc["events"][0]["sequence"] = 2
    with pytest.raises(ValidationError):
        atlas_from_dict(doc)


def test_manifest_does_not_claim_full_dynamic_replay():
    manifest = AtlasRuntime(make_atlas()).replay_manifest()
    assert manifest.scope == "DECLARED_EVENT_REPLAY"
    assert manifest.full_dynamic_replay is False
