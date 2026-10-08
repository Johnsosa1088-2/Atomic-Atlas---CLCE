"""Local explicit-review adapter to the neutral core. No LLM or semantic inference."""
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'core/src'))
from atomic_atlas_core import Atlas,Event,JsonlHashLedger,atlas_to_dict,sha256_bytes,sha256_json
from atomic_atlas_core.errors import ValidationError
from atomic_atlas_core.validation import _json_values

VERSION='ATLAS_PROPOSAL_HARNESS/0.1'

def text(value):
    if not isinstance(value,str) or not value.strip():raise ValidationError('nonempty text required')
    return value

def exact(value,keys):
    if not isinstance(value,dict) or set(value)!=set(keys):raise ValidationError('unexpected or missing fields')
    _json_values(value)

class Harness:
    def __init__(self,path,*,expected_head=None):
        self.ledger=JsonlHashLedger(path)
        self.sources={};self.proposals={};self.decisions={};self.atlas=Atlas('proposal-harness-0.1')
        records=self.ledger.records()
        head=records[-1]['head'] if records else '0'*64
        if expected_head is not None and expected_head!=head:raise ValidationError('external ledger anchor mismatch')
        self.ledger.head=head;self.ledger.count=len(records)
        for envelope in records:self._restore(envelope['record'])

    def _proposal(self,p):
        exact(p,['id','key','value','source_id','summary','summary_kind','uncertainty','supersedes','revises','truth_status'])
        for k in ['id','key','source_id','summary']:text(p[k])
        if p['summary_kind']!='SUMMARY' or p['truth_status']!='UNVERIFIED':raise ValidationError('summary/proposal status must stay explicit')
        if not isinstance(p['uncertainty'],list) or any(not isinstance(x,str) or not x.strip() for x in p['uncertainty']):raise ValidationError('uncertainty must be a text list')
        if p['supersedes'] is not None:text(p['supersedes'])
        if p['revises'] is not None:
            text(p['revises'])
            old=self.proposals.get(p['revises'])
            if old is None or old['key']!=p['key']:raise ValidationError('revision must link a prior proposal for the same key')
        if p['source_id'] not in self.sources:raise ValidationError('unknown registered source')

    def _stage(self,pid,outcome,reason,reviewer,proposal_digest,before):
        text(pid)
        if pid not in self.proposals or pid in self.decisions:raise ValidationError('unknown or already decided proposal')
        text(reason);text(reviewer)
        p=self.proposals[pid]
        if proposal_digest!=sha256_json(p):raise ValidationError('reviewed proposal digest mismatch')
        if before!=self.atlas.state_digest():raise ValidationError('stale reviewed state')
        staged=deepcopy(self.atlas);event=None
        if outcome=='ACCEPT':
            if p['uncertainty']:raise ValidationError('unresolved uncertainty blocks acceptance; submit a new linked proposal')
            current=self.atlas.state.get(p['key'])
            if current is None:
                if p['supersedes'] is not None:raise ValidationError('no current claim to supersede')
            elif p['supersedes']!=current['claim_id']:
                raise ValidationError('existing key requires explicit current claim supersession')
            claim={'claim_id':pid,'value':deepcopy(p['value']),'source':deepcopy(self.sources[p['source_id']]),'summary':p['summary'],'summary_kind':'SUMMARY','truth_status':'ACCEPTED_DECLARATION','supersedes':p['supersedes']}
            event=Event(len(staged.events)+1,'reviewed_claim_acceptance',{'state_patch':{'set':{p['key']:claim},'delete':[]}})
            staged.apply_event(event)
        elif outcome!='REJECT':raise ValidationError('outcome must be ACCEPT or REJECT')
        return staged,asdict(event) if event else None

    def _restore(self,r):
        if not isinstance(r,dict) or r.get('harness')!=VERSION:raise ValidationError('unrecognized harness record')
        kind=r.get('type')
        if kind=='source':
            exact(r,['harness','type','source']);s=r['source'];exact(s,['id','locator','text','digest']);text(s['locator']);text(s['text'])
            if s['digest']!=sha256_bytes(s['text'].encode()) or s['id']!=sha256_json({'locator':s['locator'],'digest':s['digest']}):raise ValidationError('source anchor mismatch')
            if s['id'] in self.sources:raise ValidationError('duplicate source record')
            self.sources[s['id']]=deepcopy(s)
        elif kind=='proposal':
            exact(r,['harness','type','proposal','proposal_digest']);p=r['proposal'];self._proposal(p)
            if p['id'] in self.proposals or r['proposal_digest']!=sha256_json(p):raise ValidationError('duplicate proposal or hash mismatch')
            self.proposals[p['id']]=deepcopy(p)
        elif kind=='decision':
            exact(r,['harness','type','proposal_id','outcome','reason','reviewer','proposal_digest','before_state_digest','after_state_digest','event'])
            staged,event=self._stage(r['proposal_id'],r['outcome'],r['reason'],r['reviewer'],r['proposal_digest'],r['before_state_digest'])
            if sha256_json(event)!=sha256_json(r['event']) or staged.state_digest()!=r['after_state_digest']:raise ValidationError('decision replay mismatch')
            self.atlas=staged;self.decisions[r['proposal_id']]=deepcopy(r)
        else:raise ValidationError('unknown harness record type')

    def _append(self,record):
        # Validate and replay in a detached candidate before durable append.
        candidate=object.__new__(Harness);candidate.sources=deepcopy(self.sources);candidate.proposals=deepcopy(self.proposals);candidate.decisions=deepcopy(self.decisions);candidate.atlas=deepcopy(self.atlas)
        candidate._restore(record)
        head=self.ledger.append(record)
        self.sources=candidate.sources;self.proposals=candidate.proposals;self.decisions=candidate.decisions;self.atlas=candidate.atlas
        return head

    def register_source(self,locator,source_text):
        text(locator);text(source_text);digest=sha256_bytes(source_text.encode());sid=sha256_json({'locator':locator,'digest':digest})
        if sid not in self.sources:self._append({'harness':VERSION,'type':'source','source':{'id':sid,'locator':locator,'text':source_text,'digest':digest}})
        return sid

    def propose(self,p):
        p=deepcopy(p);self._proposal(p)
        if p['id'] in self.proposals:raise ValidationError('proposal id already exists')
        digest=sha256_json(p);self._append({'harness':VERSION,'type':'proposal','proposal':p,'proposal_digest':digest})
        return digest

    def decide(self,pid,*,outcome,reason,reviewer,proposal_digest,expected_state_digest):
        staged,event=self._stage(pid,outcome,reason,reviewer,proposal_digest,expected_state_digest)
        r={'harness':VERSION,'type':'decision','proposal_id':pid,'outcome':outcome,'reason':reason,'reviewer':reviewer,'proposal_digest':proposal_digest,'before_state_digest':expected_state_digest,'after_state_digest':staged.state_digest(),'event':event}
        return self._append(r)

    def view(self):
        return deepcopy({'sources':self.sources,'proposals':self.proposals,'decisions':self.decisions,'atlas':atlas_to_dict(self.atlas),'state_digest':self.atlas.state_digest(),'ledger_head':self.ledger.head})
