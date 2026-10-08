import pytest
from atomic_atlas_core import Atlas, Entity, Relation, Route, Region, CandidateOverlay, Observation, EvidenceReference, ReplayManifest
from atomic_atlas_core.analysis import trace_route, budget_preview
from atomic_atlas_core.errors import ValidationError, RestartBlockedError
from atomic_atlas_core.interpretation import InterpretationView
from atomic_atlas_core.replay import RestartGuard, RestartStatus
from atomic_atlas_core.provenance import sha256_json


def test_candidate_overlay_stays_isolated_and_nontransporting():
    ce = Entity("candidate:a", candidate=True)
    cr = Relation("candidate:a", "candidate:b", "possible_link", candidate=True)
    overlay = CandidateOverlay("hyp-1", entities=(ce, Entity("candidate:b", candidate=True)), relations=(cr,))
    atlas = Atlas("x")
    atlas.add_candidate_overlay(overlay)
    assert not atlas.entities
    assert atlas.candidate_overlays["hyp-1"].relations[0].transport_enabled is False


def test_candidate_transport_is_rejected():
    with pytest.raises(ValidationError):
        CandidateOverlay("x", entities=(Entity("a", candidate=True), Entity("b", candidate=True)),
                         relations=(Relation("a", "b", "x", candidate=True, transport_enabled=True),))


def test_relation_does_not_imply_transport():
    r = Relation("a", "b", "declared_connection")
    assert r.transport_enabled is False
    assert r.state_mutation_enabled is False


def test_unknown_coordinates_remain_none():
    e = Entity("x", coordinates={"x": None, "y": None, "z": None})
    assert all(v is None for v in e.coordinates.values())


def test_trace_is_read_only():
    rel = [Relation("a", "b", "declared_connection")]
    result = trace_route(["a", "b"], rel)
    assert result.status == "REACHED_DECLARED_TARGET"
    assert result.state_changed is False
    assert result.transport_occurred is False


def test_trace_gate_holds_without_mutation():
    rel = [Relation("a", "b", "declared_connection")]
    result = trace_route(["a", "b"], rel, gates={"open": False}, gate_requirements={"b": "open"})
    assert result.status == "HELD"
    assert result.state_changed is False


def test_budget_preview_only_establishes_arithmetic():
    result = trace_route(["a", "b"], [Relation("a", "b", "declared_connection")])
    out = budget_preview(result, quantities={"joule": {"input": 10, "stored": 4, "heat": 6}}, evidence_id="fixture")
    assert out["status"] == "ARITHMETIC_CLOSED_HYPOTHESIS"
    assert out["physical_mechanism_established"] is False
    assert out["transport_enabled"] is False
    assert out["state_changed"] is False


def test_observation_cannot_mutate_state():
    with pytest.raises(ValidationError):
        Observation("o1", {}, EvidenceReference("fixture"), mutates_state=True)


def test_replay_scope_must_be_explicit_for_full_dynamic():
    with pytest.raises(ValidationError):
        ReplayManifest(scope="INITIAL_STRUCTURE", inputs={}, full_dynamic_replay=True)


def test_restart_guard_blocks_overwrite_until_explicit_reset():
    g = RestartGuard(expected_source_digest="a")
    assert g.check(source_digest="b", topology_digest=None, state_digest=None) == RestartStatus.BLOCKED_SOURCE_MISMATCH
    with pytest.raises(RestartBlockedError):
        g.ensure_writable()
    assert g.explicit_reset("operator accepted new lineage") == RestartStatus.RESET_AFTER_BLOCKED_RESTART


def test_interpretation_aliases_are_reversible_one_to_one():
    view = InterpretationView({"a": "alpha", "b": "beta"})
    assert view.project(["a"])[0] == {"source_id": "a", "alias": "alpha"}
    with pytest.raises(ValidationError):
        InterpretationView({"a": "same", "b": "same"})


def test_profile_semantics_are_not_required_by_core():
    atlas = Atlas("x")
    atlas.add_region(Region("r"))
    atlas.add_entity(Entity("e", region_id="r"))
    assert atlas.profile_id is None


def test_snapshot_excludes_candidate_overlays_and_observations_from_established_state():
    atlas = Atlas("x")
    atlas.add_region(Region("r"))
    atlas.add_entity(Entity("e", region_id="r"))
    atlas.record_observation(Observation("o", {"value": 1}, EvidenceReference("fixture")))
    atlas.add_candidate_overlay(CandidateOverlay("c", entities=(Entity("ce", candidate=True),)))
    snap = atlas.snapshot()
    assert "candidate_overlays" not in snap.state
    assert "observations" not in snap.state


def test_digest_is_deterministic_content_fingerprint():
    assert sha256_json({"b": 2, "a": 1}) == sha256_json({"a": 1, "b": 2})
