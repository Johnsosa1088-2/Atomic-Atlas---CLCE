"""Run with python -I in a fresh wheel-only environment, from outside this source tree."""
from pathlib import Path
import hashlib,json,importlib.metadata as meta
from importlib.resources import files
from atomic_atlas_core import Atlas,AtlasRuntime,Event,validate_contract,replay_declared_events
import atomic_atlas_core
schemas=files('atomic_atlas_core').joinpath('schemas')
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(schemas.iterdir(),key=lambda p:p.name) if p.name.endswith('.schema.json')}
assert len(hashes)==12
assert meta.version('atomic-atlas-core')=='0.0.5.dev1'
validate_contract('entity',{'id':'wheel-check'})
a=Atlas('wheel-check',state={'x':0});r=AtlasRuntime(a)
e=r.apply_state_event(event_type='set',set_values={'x':1})
assert replay_declared_events(Atlas('wheel-check',state={'x':0}),[e]).state=={'x':1}
from tempfile import TemporaryDirectory
with TemporaryDirectory() as tmp:
 p=Path(tmp)/'state.json';r.save(p);loaded=AtlasRuntime.load(p)
 assert loaded.atlas.state_digest()==a.state_digest()
assert 'site-packages' in str(Path(atomic_atlas_core.__file__))
print(json.dumps({'installed_version':meta.version('atomic-atlas-core'),'schema_count':len(hashes),'schema_byte_hashes':hashes,'source_tree_isolation':'PASS (-I, wheel-only venv)','build_validate_event_replay_save_load':'PASS'},indent=2))
