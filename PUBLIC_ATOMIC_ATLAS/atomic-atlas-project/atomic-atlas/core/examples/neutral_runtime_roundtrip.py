from pathlib import Path
from atomic_atlas_core import (
    AtlasRuntime, JsonlHashLedger, NeutralProfile, Observation, EvidenceReference,
    build_atlas, atlas_from_dict, atlas_to_dict,
)

spec = {
    "schema": "ATLAS_BUILD_SPEC/0.1",
    "version": "example-0.1",
    "regions": [{"id": "zone-a"}],
    "entities": [
        {"id": "source", "region_id": "zone-a"},
        {"id": "sink", "region_id": "zone-a"},
    ],
    "relations": [{"source": "source", "target": "sink", "type": "declared_connection"}],
    "routes": [{"id": "route-1", "entity_ids": ["source", "sink"]}],
    "initial_state": {"mode": "idle"},
}

atlas = build_atlas(spec)
profile = NeutralProfile("example-profile", possible=("idle", "active"), preferred=("idle",), required=())
ledger = JsonlHashLedger(Path("generated/example_ledger.jsonl"))
runtime = AtlasRuntime(atlas, profile=profile, ledger=ledger)
runtime.record_observation(Observation("obs-1", {"note": "fixture only"}, EvidenceReference("fixture")))
runtime.apply_state_event(event_type="mode_change", set_values={"mode": "active"})
roundtrip = atlas_from_dict(atlas_to_dict(runtime.atlas))
assert roundtrip.state == {"mode": "active"}
print(runtime.replay_manifest())
