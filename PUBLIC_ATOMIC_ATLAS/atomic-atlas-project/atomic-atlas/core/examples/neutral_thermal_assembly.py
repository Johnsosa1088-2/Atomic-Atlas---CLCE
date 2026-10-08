from atomic_atlas_core import Atlas, Entity, Relation, Region
from atomic_atlas_core.analysis import trace_route, budget_preview

atlas = Atlas(version="0.0.1.dev1")
atlas.add_region(Region("loop"))
atlas.add_entity(Entity("reservoir", type="container", region_id="loop"))
atlas.add_entity(Entity("exchanger", type="component", region_id="loop"))
atlas.add_relation(Relation("reservoir", "exchanger", type="declared_connection"))

trace = trace_route(["reservoir", "exchanger"], atlas.relations)
preview = budget_preview(
    trace,
    quantities={"joule": {"input": 10, "stored": 4, "heat": 6}},
    evidence_id="example-only",
)

assert trace.state_changed is False
assert trace.transport_occurred is False
assert preview["physical_mechanism_established"] is False
