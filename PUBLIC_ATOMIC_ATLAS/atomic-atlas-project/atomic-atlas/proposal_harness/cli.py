"""Explicit local review CLI; never infers a claim or automatically accepts one."""
import argparse,json
from pathlib import Path
from harness import Harness
from atomic_atlas_core.strict_json import loads_strict_json
p=argparse.ArgumentParser();p.add_argument('--ledger',required=True);p.add_argument('--expected-head')
sub=p.add_subparsers(dest='command',required=True)
s=sub.add_parser('source');s.add_argument('--locator',required=True);s.add_argument('--text-file',required=True)
s=sub.add_parser('propose');s.add_argument('--json-file',required=True)
s=sub.add_parser('decide');s.add_argument('--proposal-id',required=True);s.add_argument('--outcome',choices=['ACCEPT','REJECT'],required=True);s.add_argument('--reason',required=True);s.add_argument('--reviewer',required=True);s.add_argument('--proposal-digest',required=True);s.add_argument('--state-digest',required=True)
sub.add_parser('view');a=p.parse_args();h=Harness(a.ledger,expected_head=a.expected_head)
if a.command=='source':result={'source_id':h.register_source(a.locator,Path(a.text_file).read_text(encoding='utf-8'))}
elif a.command=='propose':result={'proposal_digest':h.propose(loads_strict_json(Path(a.json_file).read_bytes()))}
elif a.command=='decide':result={'ledger_head':h.decide(a.proposal_id,outcome=a.outcome,reason=a.reason,reviewer=a.reviewer,proposal_digest=a.proposal_digest,expected_state_digest=a.state_digest)}
else:result=h.view()
print(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False))
