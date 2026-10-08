import pathlib,sys,tempfile,json,subprocess,os
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from atomic_atlas_core import *
with tempfile.TemporaryDirectory() as tmp:
 p=pathlib.Path(tmp)
 baseline=build_atlas({'schema':'ATLAS_BUILD_SPEC/0.1','version':'audit-v1','entities':[{'id':'tank'},{'id':'valve'}],'relations':[{'source':'tank','target':'valve','type':'declared_connection'}],'initial_state':{'mode':'idle'}})
 runtime=AtlasRuntime(atlas_from_dict(atlas_to_dict(baseline)),ledger=JsonlHashLedger(p/'ledger.jsonl'))
 runtime.apply_state_event(event_type='operator_declared_change',set_values={'mode':'active'})
 runtime.save(p/'state.json');(p/'baseline.json').write_text(json.dumps(atlas_to_dict(baseline)))
 expected={'source':runtime.atlas.source_digest(),'topology':runtime.atlas.topology_digest(),'state':runtime.atlas.state_digest(),'ledger_head':runtime.ledger.head,'event_count':1}
 code='''import pathlib,sys,json
from atomic_atlas_core import *
p=pathlib.Path(sys.argv[1]);r=AtlasRuntime.load(p/'state.json');b=atlas_from_dict(json.loads((p/'baseline.json').read_text()));replay=replay_declared_events(b,r.atlas.events)
assert replay.state_digest()==r.atlas.state_digest()
print(json.dumps({'source':r.atlas.source_digest(),'topology':r.atlas.topology_digest(),'state':r.atlas.state_digest(),'ledger_head':JsonlHashLedger(p/'ledger.jsonl').head,'event_count':len(r.atlas.events)}))
'''
 env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
 run=subprocess.run([sys.executable,'-c',code,str(p)],env=env,text=True,capture_output=True,check=True)
 actual=json.loads(run.stdout);assert actual==expected
 report={'result':'PASS','process':'fresh Python subprocess','recovered':actual,'declared_event_replay':'PASS','full_dynamic_replay':False,'language_model_recall_tested':False,'source_bytes_used':'clean release project 007 / core 0.0.5.dev1'}
 (ROOT/'audit/FRESH_SESSION_RESULT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
