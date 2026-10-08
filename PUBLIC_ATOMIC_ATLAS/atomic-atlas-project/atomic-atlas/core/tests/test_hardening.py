import json,os,pathlib,subprocess,sys
from unittest.mock import patch
import pytest
from atomic_atlas_core import *
from atomic_atlas_core.errors import ValidationError,RestartBlockedError


def test_f01_fresh_guard_checks_before_touching_destination(tmp_path):
 p=tmp_path/'state.json';p.write_text('existing bytes')
 runtime=AtlasRuntime(Atlas('v'))
 with pytest.raises(RestartBlockedError):runtime.save(p,guard=RestartGuard(expected_source_digest='0'*64))
 assert p.read_text()=='existing bytes'
 assert not (tmp_path/'state.json.tmp').exists()


def test_f01_loaded_blocked_guard_remains_attached(tmp_path):
 p=tmp_path/'state.json';AtlasRuntime(Atlas('v')).save(p)
 runtime=AtlasRuntime.load(p,guard=RestartGuard(expected_state_digest='0'*64))
 before=p.read_bytes()
 with pytest.raises(RestartBlockedError):runtime.save(p)
 assert p.read_bytes()==before


def test_explicit_reset_accepts_new_lineage(tmp_path):
 runtime=AtlasRuntime(Atlas('v'));g=RestartGuard(expected_source_digest='0'*64)
 with pytest.raises(RestartBlockedError):runtime.save(tmp_path/'state.json',guard=g)
 g.explicit_reset('accept new lineage after inspection')
 runtime.save(tmp_path/'state.json',guard=g)
 assert (tmp_path/'state.json').exists()


def test_f02_input_returned_event_and_state_are_independent():
 values={'nested':{'x':1}};runtime=AtlasRuntime(Atlas('v'))
 event=runtime.apply_state_event(event_type='set',set_values=values)
 values['nested']['x']=2;event.payload['state_patch']['set']['nested']['x']=3
 assert runtime.atlas.state['nested']['x']==1
 assert runtime.atlas.events[0].payload['state_patch']['set']['nested']['x']==1
 runtime.atlas.state['nested']['x']=4
 assert runtime.atlas.events[0].payload['state_patch']['set']['nested']['x']==1


def test_constructor_state_and_direct_event_input_are_copied():
 original={'nested':{'x':1}};atlas=Atlas('v',state=original);original['nested']['x']=2
 assert atlas.state['nested']['x']==1
 event=Event(1,'set',{'state_patch':{'set':{'nested':{'x':3}}}});atlas.apply_event(event)
 event.payload['state_patch']['set']['nested']['x']=9
 assert atlas.state['nested']['x']==3
 assert atlas.events[0].payload['state_patch']['set']['nested']['x']==3


class FailingLedger:
 def append(self,record):raise OSError('injected ledger failure')


def test_f03_failed_state_write_keeps_state_event_and_identity():
 atlas=Atlas('v',state={'x':0});runtime=AtlasRuntime(atlas,ledger=FailingLedger());before=atlas.state_digest()
 with pytest.raises(OSError):runtime.apply_state_event(event_type='set',set_values={'x':1})
 assert runtime.atlas is atlas and atlas.state_digest()==before and atlas.events==[]


def test_failed_observation_and_overlay_writes_are_unpublished():
 atlas=Atlas('v');runtime=AtlasRuntime(atlas,ledger=FailingLedger())
 with pytest.raises(OSError):runtime.record_observation(Observation('o',{},EvidenceReference('fixture')))
 with pytest.raises(OSError):runtime.attach_candidate_overlay(CandidateOverlay('c',entities=(Entity('c1',candidate=True),)))
 assert atlas.observations==[] and atlas.candidate_overlays=={}


def test_successful_event_keeps_original_atlas_identity(tmp_path):
 atlas=Atlas('v');runtime=AtlasRuntime(atlas,ledger=JsonlHashLedger(tmp_path/'events.jsonl'))
 runtime.apply_state_event(event_type='set',set_values={'x':1})
 assert runtime.atlas is atlas and atlas.state=={'x':1} and runtime.ledger.count==1


def test_f04_direction_reversibility_and_candidate_exclusion():
 relation=Relation('a','b','link',directed=True)
 assert trace_route(['a','b'],[relation]).status=='REACHED_DECLARED_TARGET'
 assert trace_route(['b','a'],[relation]).status=='CUT'
 assert trace_route(['b','a'],[Relation('a','b','link',directed=True,reversible=True)]).status=='REACHED_DECLARED_TARGET'
 assert trace_route(['b','a'],[Relation('a','b','link')]).status=='REACHED_DECLARED_TARGET'
 assert trace_route(['a','b'],[Relation('a','b','link',candidate=True)]).status=='CUT'
 assert trace_route(['a','b'],[relation],cut_edges=[('b','a')]).status=='CUT'


def test_f05_candidate_references_accept_established_and_same_overlay():
 a=Atlas('v');a.add_entity(Entity('established'))
 a.add_candidate_overlay(CandidateOverlay('c',entities=(Entity('new',candidate=True),),relations=(Relation('established','new','possible',candidate=True),),routes=(Route('route',('established','new')),)))
 a.validate_integrity();assert set(a.entities)=={'established'}


def test_f05_rejects_unknown_shadow_duplicate_and_cross_overlay_references():
 a=Atlas('v');a.add_entity(Entity('e'));a.add_candidate_overlay(CandidateOverlay('first',entities=(Entity('other',candidate=True),)))
 cases=[CandidateOverlay('missing',relations=(Relation('e','missing','possible',candidate=True),)),CandidateOverlay('shadow',entities=(Entity('e',candidate=True),)),CandidateOverlay('dup',entities=(Entity('new',candidate=True),Entity('new',candidate=True))),CandidateOverlay('cross',relations=(Relation('e','other','possible',candidate=True),)),CandidateOverlay('route',routes=(Route('r',('missing',)),))]
 for overlay in cases:
  with pytest.raises(ValidationError):a.add_candidate_overlay(overlay)
 assert set(a.candidate_overlays)=={'first'}


def test_f06_stale_writer_is_rejected_without_corrupting_bytes(tmp_path):
 p=tmp_path/'events.jsonl';first=JsonlHashLedger(p);second=JsonlHashLedger(p)
 first.append({'a':1});before=p.read_bytes()
 with pytest.raises(ValidationError):second.append({'b':2})
 assert p.read_bytes()==before and JsonlHashLedger(p).count==1
 third=JsonlHashLedger(p);third.append({'c':3});assert JsonlHashLedger(p).count==2


def test_f06_lock_excludes_another_process(tmp_path):
 p=tmp_path/'events.jsonl';ledger=JsonlHashLedger(p)
 env=dict(os.environ,PYTHONPATH=str(pathlib.Path(__file__).resolve().parents[1]/'src'))
 code="from atomic_atlas_core import JsonlHashLedger;from atomic_atlas_core.errors import ValidationError;import sys\ntry: JsonlHashLedger(sys.argv[1])\nexcept ValidationError: print('BLOCKED')\nelse: raise AssertionError('writer was not excluded')"
 with ledger._locked():
  out=subprocess.run([sys.executable,'-c',code,str(p)],env=env,text=True,capture_output=True,check=True)
  assert out.stdout.strip()=='BLOCKED'
 assert not pathlib.Path(str(p)+'.lock').exists()


def test_f06_fsync_failure_rolls_back_file_and_runtime(tmp_path):
 p=tmp_path/'events.jsonl';ledger=JsonlHashLedger(p);ledger.append({'seed':1});before=p.read_bytes()
 runtime=AtlasRuntime(Atlas('v',state={'x':0}),ledger=ledger)
 with patch('atomic_atlas_core.ledger.os.fsync',side_effect=OSError('injected fsync error')):
  with pytest.raises(OSError):runtime.apply_state_event(event_type='set',set_values={'x':1})
 assert p.read_bytes()==before and runtime.atlas.state=={'x':0} and runtime.atlas.events==[]
 assert JsonlHashLedger(p).count==1 and ledger.count==1


def test_incomplete_tail_rejected_without_modifying_file(tmp_path):
 p=tmp_path/'events.jsonl';p.write_bytes(b'{')
 with pytest.raises(ValidationError):JsonlHashLedger(p)
 assert p.read_bytes()==b'{' and not pathlib.Path(str(p)+'.lock').exists()


def test_f07_dirty_baseline_rejected_without_modifying_baseline():
 a=Atlas('v',state={'x':0});a.apply_event(Event(1,'set',{'state_patch':{'set':{'x':1}}}))
 before=atlas_to_dict(a)
 with pytest.raises(ValidationError):replay_declared_events(a,[])
 assert atlas_to_dict(a)==before


def test_replay_clean_baseline_recovers_state_and_preserves_inputs():
 baseline=Atlas('v',state={'x':0});runtime=AtlasRuntime(atlas_from_dict(atlas_to_dict(baseline)))
 runtime.apply_state_event(event_type='set',set_values={'nested':{'x':1}})
 runtime.apply_state_event(event_type='delete',delete_keys=('x',))
 replayed=replay_declared_events(baseline,runtime.atlas.events)
 assert replayed.state_digest()==runtime.atlas.state_digest()
 replayed.state['nested']['x']=9
 assert runtime.atlas.state['nested']['x']==1 and baseline.state=={'x':0}


def test_invalid_patch_does_not_partially_update_state():
 a=Atlas('v',state={'x':0})
 with pytest.raises(ValidationError):a.apply_event(Event(1,'bad',{'state_patch':{'set':{'x':1},'delete':[None]}}))
 assert a.state=={'x':0} and a.events==[]


def test_import_export_and_snapshot_do_not_leak_nested_state_references():
 runtime=AtlasRuntime(Atlas('v',state={'nested':{'x':1}}))
 runtime.apply_state_event(event_type='set',set_values={'nested':{'x':2}})
 doc=runtime.document();doc['state']['nested']['x']=9
 doc['events'][0]['payload']['state_patch']['set']['nested']['x']=9
 assert runtime.atlas.state['nested']['x']==2
 assert runtime.atlas.events[0].payload['state_patch']['set']['nested']['x']==2
 imported=atlas_from_dict(runtime.document());incoming=runtime.document();loaded=atlas_from_dict(incoming)
 incoming['events'][0]['payload']['state_patch']['set']['nested']['x']=10
 assert loaded.events[0].payload['state_patch']['set']['nested']['x']==2
 snap=runtime.atlas.snapshot();snap.state['runtime_state']['nested']['x']=11
 assert runtime.atlas.state['nested']['x']==2 and imported.state['nested']['x']==2


def test_rejected_candidate_integrity_is_checked_on_loaded_document():
 a=Atlas('v');a.add_entity(Entity('e'))
 doc=atlas_to_dict(a)
 doc['candidate_overlays']=[{'id':'c','entities':[],'relations':[{'source':'e','target':'missing','type':'possible','candidate':True}],'routes':[],'status':'candidate'}]
 with pytest.raises(ValidationError):atlas_from_dict(doc)
