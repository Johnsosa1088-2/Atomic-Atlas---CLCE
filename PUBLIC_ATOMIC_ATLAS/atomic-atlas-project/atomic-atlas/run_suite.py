"""Verify archive anchors and run the available release suites (pytest/jsonschema/Node required)."""
from pathlib import Path
import hashlib,json,subprocess,sys,os
root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'step10/check_inventory.py')],check=True)
subprocess.run([sys.executable,str(root/'step10/test_inventory.py')],check=True)
subprocess.run([sys.executable,str(root/'step10/test_freeze_portability.py')],check=True)
m=json.loads((root/'RELEASE_MANIFEST.json').read_text())
for name,digest in m['files'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
commands=[('step8',[sys.executable,'check_source_freeze.py']),('step8',[sys.executable,'-m','pytest','tests','-q']),('step7',[sys.executable,'mutation_controls.py']),('proposal_harness',[sys.executable,'-m','pytest','tests','-q']),('proposal_harness',[sys.executable,'demo.py']),('core',[sys.executable,'-m','pytest','-q']),('core',[sys.executable,'audit/independent/check_conformance.py']),('core',[sys.executable,'audit/run_tests.py']),('core',[sys.executable,'audit/fresh_session_check.py']),('examples/a_soft_robotic_finger',[sys.executable,'run_example_a_test.py']),('examples/b_atlas_retrieval',[sys.executable,'-m','unittest','discover','-s','tests','-v']),('examples/b_atlas_retrieval',['node','tests/test_engine.js']),('examples/b_atlas_retrieval',['node','tests/dom_check.js']),('examples/c_closed_loop_budget',['node','--test','tests/test.js'])]
env=dict(os.environ,PYTHONPATH=str(root/'core/src'))
for directory,command in commands:
    subprocess.run(command,cwd=root/directory,env=env,check=True)
subprocess.run([sys.executable,'step8/check_source_freeze.py'],cwd=root,check=True)
print('Candidate integrity and full available release check suites passed. Wheel isolation is separately reproducible; Windows/browser remain untested.')
