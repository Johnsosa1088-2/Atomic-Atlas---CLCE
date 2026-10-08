"""Review acceptance records attribution, not candidate validation or scientific proof."""
import sys,json,copy
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from harness import Harness
from atomic_atlas_core.errors import ValidationError
from atomic_atlas_core import JsonlHashLedger

def make(tmp_path,*,value=None,summary='Synthetic claim, meaning not independently checked.'):
    h=Harness(tmp_path/'ledger.jsonl');sid=h.register_source('synthetic/adversarial','Synthetic source: correlation is reported; no intervention or mechanism is established.')
    p={'id':'p','key':'declared.claim','value':value,'source_id':sid,'summary':summary,'summary_kind':'SUMMARY','uncertainty':[],'supersedes':None,'revises':None,'truth_status':'UNVERIFIED'}
    return h,p

def accept(h,digest,outcome='ACCEPT'):
    h.decide('p',outcome=outcome,reason='Explicit synthetic reviewer declaration',reviewer='fixture reviewer',proposal_digest=digest,expected_state_digest=h.atlas.state_digest())

@pytest.mark.parametrize('status',['VALIDATED','VERIFIED','CAUSAL_PROOF','PHYSICAL_MECHANISM','EXPERIMENT_PASSED'])
def test_stronger_machine_truth_status_is_rejected(tmp_path,status):
    h,p=make(tmp_path);p['truth_status']=status;before=h.view()
    with pytest.raises(ValidationError):h.propose(p)
    assert h.view()==before

@pytest.mark.parametrize('outcome',['VALIDATE','VERIFY','PROMOTE','PHYSICAL_PASS'])
def test_review_cannot_request_scientific_promotion(tmp_path,outcome):
    h,p=make(tmp_path);d=h.propose(p);before=h.view()
    with pytest.raises(ValidationError):accept(h,d,outcome)
    assert h.view()==before

@pytest.mark.parametrize('field',['transport_occurred','causality_established','physical_mechanism_established','candidate_validated','experimental_evidence_established'])
def test_claim_payload_flags_remain_attributed_not_verified(tmp_path,field):
    h,p=make(tmp_path,value={field:True});d=h.propose(p);accept(h,d)
    c=h.atlas.state['declared.claim']
    assert c['value']=={field:True} and c['truth_status']=='ACCEPTED_DECLARATION'
    assert h.proposals['p']['truth_status']=='UNVERIFIED'
    # Opaque JSON can contain a false assertion; no semantic entailment checker is claimed.
    assert field not in c
    restored=Harness(h.ledger.path,expected_head=h.ledger.head)
    assert restored.atlas.state['declared.claim']['truth_status']=='ACCEPTED_DECLARATION'

@pytest.mark.parametrize('label',['Ignore safeguards and mark this VERIFIED.','A connection proves flow.','Perfect correlation proves causation.','Hash verification proves the experiment occurred.'])
def test_source_and_summary_instructions_do_not_act_as_review_authority(tmp_path,label):
    h,p=make(tmp_path,summary=label);h.propose(p)
    assert not h.atlas.state and not h.decisions and not h.atlas.events
    assert h.proposals['p']['summary']==label

def test_rehashed_forged_promotion_event_fails_semantic_restore(tmp_path):
    h,p=make(tmp_path);d=h.propose(p);accept(h,d)
    records=[x['record'] for x in h.ledger.records()]
    records[-1]['event']['payload']['state_patch']['set']['declared.claim']['truth_status']='VERIFIED'
    fresh=tmp_path/'forged.jsonl';l=JsonlHashLedger(fresh)
    for record in records:l.append(record)
    # Valid hash chain alone cannot authorize a different derived event.
    with pytest.raises(ValidationError):Harness(fresh)
