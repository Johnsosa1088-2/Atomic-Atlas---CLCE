import json
import subprocess
import sys
import tempfile
from pathlib import Path
from atlas_store import Store

if len(sys.argv) == 3 and sys.argv[1] == 'recover':
    store = Store(sys.argv[2])
    print(json.dumps(store.recover('lamp'), sort_keys=True))
    store.close()
else:
    with tempfile.TemporaryDirectory() as directory:
        path = str(Path(directory) / 'demo.sqlite')
        store = Store(path)
        anchor = store.append('demo-001', 'lamp', {'power': {'value': 5, 'unit': 'W'}, 'enabled': True},
                              {'locator': 'synthetic:demo/lamp', 'evidence': 'synthetic'}, None)
        before = store.recover('lamp')
        store.close()
        after = json.loads(subprocess.check_output([sys.executable, __file__, 'recover', path], text=True))
        assert before == after
        print(json.dumps({'fresh_process_recovery': 'PASS', 'anchor': anchor, 'recovered': after}, indent=2))
