"""Check the immutable implementation/schema/wheel anchors inherited from project 007."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
anchors=json.loads((ROOT/'step8/FROZEN_IMPLEMENTATION.json').read_text())
actual={p.relative_to(ROOT).as_posix() for directory in ['core/src','core/schemas','distributions'] for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
actual.add('core/pyproject.toml')
actual.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'proposal_harness').glob('*.py'))
assert actual==set(anchors['files']),'frozen implementation file inventory changed'
for name,digest in anchors['files'].items():
 assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
print(json.dumps({'result':'PASS','frozen_files':len(anchors['files']),'core_harness_schemas_wheel_unchanged':True}))
