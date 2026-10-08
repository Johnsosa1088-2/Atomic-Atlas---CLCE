import copy,json,subprocess,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from harness import Harness
from atomic_atlas_core.errors import ValidationError
from atomic_atlas_core import JsonlHashLedger,sha256_json

@pytest.fixture
def h(tmp_path):return Harness(tmp_path/'review.jsonl')

def proposal(h,id='p1',value=10,**extras):
    sid=h.register_source('synthetic/manual-A','Synthetic fixture: valve setting is 10. Unit not supplied.')
    return dict(id=id,key='valve.setting',value=value,source_id=sid,summary='Manual A reports a valve setting of 10; no unit is supplied.',summary_kind='SUMMARY',uncertainty=[],supersedes=None,revises=None,truth_status='UNVERIFIED',**extras)

def decide(h,pid,digest,outcome='ACCEPT'):
    return h.decide(pid,outcome=outcome,reason='Explicit synthetic review',reviewer='fixture reviewer',proposal_digest=digest,expected_state_digest=h.atlas.state_digest())

def test_proposal_does_not_change_established_state(h):
    before=h.atlas.state_digest();p=proposal(h);h.propose(p)
    assert h.atlas.state_digest()==before and h.atlas.events==[] and not h.decisions

def test_acceptance_uses_core_event_and_keeps_source_and_summary(h):
    p=proposal(h);d=h.propose(p);decide(h,'p1',d)
    c=h.atlas.state['valve.setting'];assert c['value']==10 and c['truth_status']=='ACCEPTED_DECLARATION' and c['summary_kind']=='SUMMARY'
    assert c['source']['locator']=='synthetic/manual-A' and len(h.atlas.events)==1

def test_rejection_preserves_state_and_receipt(h):
    p=proposal(h);d=h.propose(p);before=h.atlas.state_digest();decide(h,'p1',d,'REJECT')
    assert h.atlas.state_digest()==before and h.decisions['p1']['event'] is None

def test_contradiction_requires_explicit_current_supersession(h):
    d=h.propose(proposal(h));decide(h,'p1',d);d2=h.propose(proposal(h,'p2',12));before=h.view()
    with pytest.raises(ValidationError):decide(h,'p2',d2)
    assert h.view()==before

def test_correction_is_append_only_and_linked(h):
    d=h.propose(proposal(h));decide(h,'p1',d);first=copy.deepcopy(h.proposals['p1']);old=h.ledger.path.read_bytes()
    p=proposal(h,'p2',12);p.update(supersedes='p1',revises='p1',summary='Synthetic reviewer corrects the setting to 12; unit remains unspecified.')
    d=h.propose(p);decide(h,'p2',d)
    assert h.proposals['p1']==first and h.ledger.path.read_bytes().startswith(old)
    assert h.atlas.state['valve.setting']['supersedes']=='p1'

def test_uncertainty_blocks_acceptance_and_revision_can_resolve_it(h):
    p=proposal(h);p['uncertainty']=['Setting might mean a range'];d=h.propose(p)
    with pytest.raises(ValidationError):decide(h,'p1',d)
    decide(h,'p1',d,'REJECT')
    p2=proposal(h,'p2');p2['revises']='p1';d2=h.propose(p2);decide(h,'p2',d2)
    assert h.atlas.state['valve.setting']['claim_id']=='p2'

@pytest.mark.parametrize('field,value',[('truth_status','VERIFIED'),('summary_kind','EXACT_QUOTE'),('source_id','missing'),('uncertainty','unknown'),('value',float('nan')),('revises','missing')])
def test_invalid_proposals_never_append(h,field,value):
    p=proposal(h);p[field]=value;before=h.view();raw=h.ledger.path.read_bytes()
    with pytest.raises(ValidationError):h.propose(p)
    assert h.view()==before and h.ledger.path.read_bytes()==raw

def test_unknown_fields_rejected(h):
    p=proposal(h);p['unapproved']='field'
    with pytest.raises(ValidationError):h.propose(p)

def test_review_is_bound_to_proposal_and_state_hashes(h):
    d=h.propose(proposal(h));before=h.view()
    with pytest.raises(ValidationError):decide(h,'p1','0'*64)
    with pytest.raises(ValidationError):h.decide('p1',outcome='ACCEPT',reason='review',reviewer='test',proposal_digest=d,expected_state_digest='0'*64)
    assert h.view()==before

def test_duplicate_id_and_duplicate_decision_rejected(h):
    p=proposal(h);d=h.propose(p)
    with pytest.raises(ValidationError):h.propose(p)
    decide(h,'p1',d)
    with pytest.raises(ValidationError):decide(h,'p1',d)

def test_ledger_failure_does_not_publish_decision(h):
    from unittest.mock import patch
    d=h.propose(proposal(h));before=h.view()
    with patch.object(h.ledger,'append',side_effect=OSError('injected')):
        with pytest.raises(OSError):decide(h,'p1',d)
    assert h.view()==before

def test_stale_process_cannot_publish(h):
    d=h.propose(proposal(h));stale=Harness(h.ledger.path);decide(h,'p1',d);before=stale.view()
    with pytest.raises(ValidationError):decide(stale,'p1',d)
    assert stale.view()==before

def test_independent_anchor_mismatch_rejected(h):
    h.propose(proposal(h))
    with pytest.raises(ValidationError):Harness(h.ledger.path,expected_head='0'*64)

def test_recovery_in_fresh_process_matches_state_and_head(h):
    d=h.propose(proposal(h));decide(h,'p1',d)
    module=str(Path(__file__).resolve().parents[1])
    code="import sys,json;sys.path.insert(0,sys.argv[1]);from harness import Harness;h=Harness(sys.argv[2],expected_head=sys.argv[3]);print(json.dumps({'state':h.atlas.state_digest(),'head':h.ledger.head}))"
    result=subprocess.run([sys.executable,'-c',code,module,str(h.ledger.path),h.ledger.head],text=True,capture_output=True,check=True)
    assert json.loads(result.stdout)=={'state':h.atlas.state_digest(),'head':h.ledger.head}

def test_semantically_invalid_rehashed_chain_is_rejected(tmp_path):
    l=JsonlHashLedger(tmp_path/'bad.jsonl');l.append({'harness':'ATLAS_PROPOSAL_HARNESS/0.1','type':'decision'})
    with pytest.raises(ValidationError):Harness(l.path)

def test_detached_inputs_and_views(h):
    p=proposal(h,value={'setting':10});d=h.propose(p);p['value']['setting']=99;decide(h,'p1',d)
    view=h.view();view['atlas']['state']['valve.setting']['value']['setting']=88
    assert h.atlas.state['valve.setting']['value']=={'setting':10}

def test_cli_explicit_review_roundtrip(tmp_path):
    cli=Path(__file__).resolve().parents[1]/'cli.py';ledger=tmp_path/'cli ledger.jsonl';source=tmp_path/'manual.txt';source.write_text('Synthetic manual: setting 10, no supplied unit.')
    def run(*args):
        result=subprocess.run([sys.executable,str(cli),'--ledger',str(ledger),*args],text=True,capture_output=True,check=True)
        return json.loads(result.stdout)
    sid=run('source','--locator','synthetic/cli','--text-file',str(source))['source_id']
    p={'id':'p','key':'valve.setting','value':10,'source_id':sid,'summary':'Synthetic setting 10; unit unspecified.','summary_kind':'SUMMARY','uncertainty':[],'supersedes':None,'revises':None,'truth_status':'UNVERIFIED'}
    path=tmp_path/'proposal.json';path.write_text(json.dumps(p));d=run('propose','--json-file',str(path))['proposal_digest'];v=run('view')
    assert v['atlas']['state']=={}
    run('decide','--proposal-id','p','--outcome','ACCEPT','--reason','Manual fixture review','--reviewer','synthetic','--proposal-digest',d,'--state-digest',v['state_digest'])
    assert run('view')['atlas']['state']['valve.setting']['value']==10
