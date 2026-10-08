"""Same tests/API for heterogeneous synthetic domains; no domain-name branching."""
from pathlib import Path
from dataclasses import asdict
from copy import deepcopy
import sys,json,os,subprocess
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'core/src'));sys.path.insert(0,str(ROOT/'proposal_harness'))
from atomic_atlas_core import *
from atomic_atlas_core.errors import ValidationError
from harness import Harness
CASES=json.loads((ROOT/'step8/domains.json').read_text())
@pytest.fixture(params=CASES,ids=lambda c:c['id'])
def case(request):return deepcopy(request.param)

def make(c):return AtlasRuntime(build_atlas(c['spec']),profile=load_profile_dict(c['profile']))
def route(r,c):return r.atlas.routes[c['route_id']].entity_ids

def test_schema_build_profile_document_roundtrip(case):
 r=make(case);r.atlas.validate_integrity();validate_contract('build-spec',case['spec']);validate_contract('neutral-profile',case['profile']);validate_contract('document',r.document());validate_contract('topology',r.atlas.topology_payload());validate_contract('state-snapshot',asdict(r.atlas.snapshot()));validate_contract('replay-manifest',asdict(r.replay_manifest()))
 other=atlas_from_dict(r.document());assert other.topology_digest()==r.atlas.topology_digest() and other.state_digest()==r.atlas.state_digest()
 assert r.profile.possible!=r.profile.required and all(e.coordinates['x'] is None and e.attributes['measurement'] is None for e in other.entities.values())

def test_route_gate_cut_and_closed_preview_are_declarative(case):
 r=make(case);path=route(r,case);before=r.document();rels=r.atlas.relations
 trace=trace_route(path,rels);assert trace.status=='REACHED_DECLARED_TARGET' and not trace.transport_occurred
 assert trace_route(path,rels,cut_edges=[path[:2]]).status=='CUT'
 assert trace_route(path,rels,gates={'permit':False},gate_requirements={path[1]:'permit'}).status=='HELD'
 assert trace_route(path,rels,gates={'permit':True},gate_requirements={path[1]:'permit'}).status=='REACHED_DECLARED_TARGET'
 budget=budget_preview(trace,quantities={case['unit']:case['budget']},evidence_id='synthetic/domain-fixture')
 assert budget['status']=='ARITHMETIC_CLOSED_HYPOTHESIS' and not budget['physical_mechanism_established'] and not budget['evidence_verified'] and r.document()==before

def test_candidate_and_observation_remain_isolated(case):
 r=make(case);before=r.atlas.state_digest();first=route(r,case)[0];cid=case['candidate_id']
 r.attach_candidate_overlay(CandidateOverlay('proposal',entities=(Entity(cid,candidate=True),),relations=(Relation(first,cid,'possible',candidate=True),)))
 r.record_observation(Observation('synthetic-observation',{'measurement':None},EvidenceReference('synthetic, not measured')))
 assert r.atlas.state_digest()==before and cid not in r.atlas.entities and not r.atlas.events
 assert trace_route([first,cid],r.atlas.candidate_overlays['proposal'].relations).status=='CUT'
 assert 'candidate_overlays' not in r.atlas.snapshot().state and 'observations' not in r.atlas.snapshot().state

def test_patch_replay_and_fresh_process_recovery(case,tmp_path):
 r=make(case);baseline=atlas_from_dict(r.document());r.ledger=JsonlHashLedger(tmp_path/'ledger.jsonl')
 r.apply_state_event(event_type='declared-mode-change',set_values={'mode':'reviewed','quantity':None})
 r.apply_state_event(event_type='declared-cleanup',delete_keys=('quantity',))
 assert replay_declared_events(baseline,r.atlas.events).state_digest()==r.atlas.state_digest()
 p=tmp_path/'state.json';r.save(p);base=tmp_path/'baseline.json';base.write_text(json.dumps(atlas_to_dict(baseline)))
 code="import sys,json;from pathlib import Path;from atomic_atlas_core import *;p=Path(sys.argv[1]);r=AtlasRuntime.load(p/'state.json');b=atlas_from_dict(json.loads((p/'baseline.json').read_text()));a=replay_declared_events(b,r.atlas.events);assert a.state_digest()==r.atlas.state_digest();print(json.dumps({'state':a.state_digest(),'topology':a.topology_digest(),'head':JsonlHashLedger(p/'ledger.jsonl').head}))"
 child=subprocess.run([sys.executable,'-c',code,str(tmp_path)],env=dict(os.environ,PYTHONPATH=str(ROOT/'core/src')),text=True,capture_output=True,check=True)
 assert json.loads(child.stdout)=={'state':r.atlas.state_digest(),'topology':r.atlas.topology_digest(),'head':r.ledger.head}

def test_unknown_endpoint_and_duplicate_identity_fail_same_integrity_rules(case):
 bad=deepcopy(case['spec']);bad['relations'][0]['target']='unknown:entity';validate_contract('build-spec',bad)
 with pytest.raises(ValidationError):build_atlas(bad)
 bad=deepcopy(case['spec']);bad['entities'].append(deepcopy(bad['entities'][0]));validate_contract('build-spec',bad)
 with pytest.raises(ValidationError):build_atlas(bad)

def test_domain_labels_and_profiles_do_not_infer_function(case):
 r=make(case);before=r.atlas.state_digest()
 assert not r.atlas.events and before==make(case).atlas.state_digest()
 assert all(not rel.transport_enabled and not rel.state_mutation_enabled for rel in r.atlas.relations)
 assert r.profile.required and r.profile.as_dict()['semantics']==case['profile']['semantics']

def test_same_review_and_supersession_workflow(case,tmp_path):
 h=Harness(tmp_path/'review.jsonl');sid=h.register_source('synthetic/'+case['id'],'Synthetic declaration: mode idle. Correction: mode reviewed.')
 def proposal(pid,value,supersedes=None,revises=None):return {'id':pid,'key':case['review_key'],'value':value,'source_id':sid,'summary':'Synthetic intended mode '+value+'; no measured behavior.','summary_kind':'SUMMARY','uncertainty':[],'supersedes':supersedes,'revises':revises,'truth_status':'UNVERIFIED'}
 def accept(pid,d):h.decide(pid,outcome='ACCEPT',reason='Synthetic explicit review',reviewer='fixture reviewer',proposal_digest=d,expected_state_digest=h.atlas.state_digest())
 before=h.atlas.state_digest();d=h.propose(proposal('p1','idle'));assert h.atlas.state_digest()==before;accept('p1',d)
 d=h.propose(proposal('p2','reviewed'));before=h.view()
 with pytest.raises(ValidationError):accept('p2',d)
 assert h.view()==before
 d=h.propose(proposal('p3','reviewed','p1','p2'));accept('p3',d)
 assert h.atlas.state[case['review_key']]['truth_status']=='ACCEPTED_DECLARATION' and h.proposals['p1']['value']=='idle'
 assert Harness(h.ledger.path,expected_head=h.ledger.head).view()==h.view()

def test_alpha_renaming_preserves_operations_but_changes_content_hashes(case):
 a=make(case);spec=deepcopy(case['spec']);ids={e['id']:'neutral-node-'+str(i) for i,e in enumerate(spec['entities'])};regions={e['id']:'neutral-region-'+str(i) for i,e in enumerate(spec['regions'])}
 for e in spec['regions']:e['id']=regions[e['id']]
 for e in spec['entities']:e['id']=ids[e['id']];e['region_id']=regions[e['region_id']];e['attributes']={}
 for rel in spec['relations']:rel['source']=ids[rel['source']];rel['target']=ids[rel['target']];rel['type']='neutral_link'
 for rr in spec['routes']:rr['entity_ids']=[ids[x] for x in rr['entity_ids']]
 spec['version']='neutral-version';spec['provenance']=[{'source_id':'synthetic/neutral'}]
 for rr in spec['routes']:rr['id']='neutral-route'
 b=build_atlas(spec)
 x=trace_route(route(a,case),a.atlas.relations);y=trace_route(b.routes['neutral-route'].entity_ids,b.relations)
 assert x.status==y.status and len(x.visited)==len(y.visited) and not y.transport_occurred
 assert a.atlas.topology_digest()!=b.topology_digest()
 a.apply_state_event(event_type='declared',set_values={'mode':'reviewed'});AtlasRuntime(b).apply_state_event(event_type='declared',set_values={'mode':'reviewed'})
 assert a.atlas.state_digest()==b.state_digest()


def test_corpus_has_eight_distinct_unlabeled_graph_shapes():
 signatures=[]
 for c in CASES:
  s=c['spec'];degree={e['id']:0 for e in s['entities']}
  for r in s['relations']:degree[r['source']]+=1;degree[r['target']]+=1
  signatures.append((len(s['entities']),len(s['relations']),tuple(sorted(degree.values()))))
 assert len(CASES)==8 and len(set(signatures))==8
 # Distinct degree/count signatures establish nonisomorphism here; names alone do not distinguish fixtures.
