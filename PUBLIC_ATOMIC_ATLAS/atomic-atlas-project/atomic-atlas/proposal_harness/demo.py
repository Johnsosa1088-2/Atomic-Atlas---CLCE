"""Temporary synthetic demonstration, or explicit new output directory; no bundled history."""
import argparse,json,tempfile
from pathlib import Path
from harness import Harness
from atomic_atlas_core.errors import ValidationError

def run(folder):
    h=Harness(folder/'review.jsonl')
    source=h.register_source('synthetic/manual-A','Synthetic fixture: valve setting is 10; unit not supplied.')
    source2=h.register_source('synthetic/manual-B','Synthetic correction: valve setting is 12; unit not supplied.')
    def proposal(pid,value,sid,supersedes=None,revises=None,uncertainty=None):
        return {'id':pid,'key':'valve.setting','value':value,'source_id':sid,'summary':'Synthetic manual reports setting '+str(value)+'; unit remains unspecified.','summary_kind':'SUMMARY','uncertainty':uncertainty or [],'supersedes':supersedes,'revises':revises,'truth_status':'UNVERIFIED'}
    def decide(pid,digest,outcome,reason):
        h.decide(pid,outcome=outcome,reason=reason,reviewer='synthetic local reviewer',proposal_digest=digest,expected_state_digest=h.atlas.state_digest())
    before=h.atlas.state_digest();d=h.propose(proposal('p1',10,source));assert before==h.atlas.state_digest()
    decide('p1',d,'ACCEPT','Reviewer accepts the attributed declaration, not independent truth.')
    d=h.propose(proposal('p2',12,source2))
    try:decide('p2',d,'ACCEPT','Attempt without explicit supersession')
    except ValidationError:pass
    else:raise AssertionError('conflict was not blocked')
    decide('p2',d,'REJECT','Correction must explicitly identify the current claim it supersedes.')
    d=h.propose(proposal('p3',12,source2,supersedes='p1',revises='p2'));decide('p3',d,'ACCEPT','Explicitly replace p1 with the source-attributed correction.')
    d=h.propose(proposal('p4',20,source2,uncertainty=['Unsupported setting, not supplied by this source']))
    try:decide('p4',d,'ACCEPT','Attempt despite unresolved uncertainty')
    except ValidationError:pass
    else:raise AssertionError('uncertainty was not blocked')
    decide('p4',d,'REJECT','The source does not support this declaration.')
    restored=Harness(folder/'review.jsonl',expected_head=h.ledger.head);assert restored.view()==h.view()
    return {'result':'PASS','cases':['proposal isolation','explicit acceptance','conflict blocking','explicit rejection','linked correction','uncertainty blocking','source-attributed rejection','ledger reconstruction'],'final_claim':h.atlas.state['valve.setting'],'event_count':len(h.atlas.events),'ledger_count':h.ledger.count,'ledger_head':h.ledger.head,'state_digest':h.atlas.state_digest(),'scope':'Synthetic manual proposals, no LLM extraction or factual truth verification.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-folder');args=p.parse_args()
    if args.output_folder:
        folder=Path(args.output_folder);folder.mkdir(parents=True,exist_ok=False);result=run(folder)
    else:
        with tempfile.TemporaryDirectory() as tmp:result=run(Path(tmp))
    print(json.dumps(result,indent=2,ensure_ascii=False))
