"""Release boundary cases: structural validity is not semantic integrity."""
import copy,json
from pathlib import Path
import pytest
from atomic_atlas_core import Atlas,AtlasRuntime,Event,JsonlHashLedger,RestartGuard,atlas_from_dict,atlas_to_dict,replay_declared_events,validate_contract
from atomic_atlas_core.errors import ValidationError,RestartBlockedError
from atomic_atlas_core.provenance import sha256_json
ROOT=Path(__file__).resolve().parents[1]

def fixture():return json.loads((ROOT/'fixtures/valid.json').read_text())['document']

def invalid_document(kind):
    d=fixture()
    if kind=='duplicate-region':d['regions'].append(copy.deepcopy(d['regions'][0]))
    elif kind=='duplicate-entity':d['entities'].append(copy.deepcopy(d['entities'][0]))
    elif kind=='unknown-region':d['entities'][0]['region_id']='missing'
    elif kind=='unknown-relation-target':d['relations'][0]['target']='missing'
    elif kind=='unknown-route-member':d['routes'][0]['entity_ids'].append('missing')
    elif kind=='duplicate-route':d['routes'].append(copy.deepcopy(d['routes'][0]))
    elif kind=='event-gap':d['events'][0]['sequence']=2
    elif kind=='duplicate-event':d['events'].append(copy.deepcopy(d['events'][0]))
    elif kind=='candidate-shadows-established':d['candidate_overlays']=[{'id':'c','entities':[{'id':'reservoir','candidate':True}]}]
    return d

@pytest.mark.parametrize('kind',['duplicate-region','duplicate-entity','unknown-region','unknown-relation-target','unknown-route-member','duplicate-route','event-gap','duplicate-event','candidate-shadows-established'])
def test_structurally_valid_documents_fail_integrity_without_input_mutation(kind):
    d=invalid_document(kind);before=copy.deepcopy(d)
    validate_contract('document',d)
    with pytest.raises(ValidationError):atlas_from_dict(d)
    assert d==before

@pytest.mark.parametrize('kind',['payload','head','previous-head','sequence','reorder','truncate'])
def test_ledger_tampering_rejected_and_bytes_preserved(tmp_path,kind):
    p=tmp_path/'ledger.jsonl';l=JsonlHashLedger(p);l.append({'x':1});l.append({'x':2})
    lines=p.read_text().splitlines();records=[json.loads(s) for s in lines]
    if kind=='payload':records[0]['record']['x']=99
    elif kind=='head':records[0]['head']='0'*64
    elif kind=='previous-head':records[1]['previous_head']='0'*64
    elif kind=='sequence':records[0]['sequence']=True
    elif kind=='reorder':records.reverse()
    if kind=='truncate':p.write_text(lines[0]+'\n'+lines[1][:-3])
    else:p.write_text(''.join(json.dumps(r)+'\n' for r in records))
    before=p.read_bytes()
    with pytest.raises(ValidationError):JsonlHashLedger(p)
    assert p.read_bytes()==before and not p.with_name(p.name+'.lock').exists()

@pytest.mark.parametrize('kind',['extra-field','missing-record'])
def test_unhashed_ledger_envelope_changes_are_rejected(tmp_path,kind):
    p=tmp_path/'ledger.jsonl';l=JsonlHashLedger(p);l.append(None)
    r=json.loads(p.read_text())
    if kind=='extra-field':r['unhashed_claim']='approved'
    else:del r['record']
    p.write_text(json.dumps(r)+'\n');before=p.read_bytes()
    with pytest.raises(ValidationError):JsonlHashLedger(p)
    assert p.read_bytes()==before

@pytest.mark.parametrize('boundary',['document','ledger'])
def test_duplicate_json_keys_rejected_at_file_boundaries(tmp_path,boundary):
    p=tmp_path/'input.json'
    if boundary=='document':
        d=fixture();raw=json.dumps(d);raw=raw.replace('"version": "fixture-v1"','"version": "hidden-version", "version": "fixture-v1"');p.write_text(raw)
        loader=lambda:AtlasRuntime.load(p)
    else:
        l=JsonlHashLedger(p);l.append({'x':1});raw=p.read_text().replace('"record":','"record":{"hidden":1},"record":');p.write_text(raw)
        loader=lambda:JsonlHashLedger(p)
    before=p.read_bytes()
    with pytest.raises(ValidationError):loader()
    assert p.read_bytes()==before

@pytest.mark.parametrize('value',[float('nan'),float('inf'),float('-inf')])
def test_nonfinite_ledger_payloads_rejected_without_append(tmp_path,value):
    p=tmp_path/'ledger.jsonl';l=JsonlHashLedger(p);l.append({'seed':1});before=p.read_bytes();head=l.head
    with pytest.raises(ValidationError):l.append({'value':value})
    assert p.read_bytes()==before and l.head==head and l.count==1

@pytest.mark.parametrize('component',['source','topology','state'])
def test_expected_digest_mismatch_blocks_save_without_overwriting(tmp_path,component):
    p=tmp_path/'state.json';runtime=AtlasRuntime(Atlas('v',state={'x':0}));runtime.save(p);before=p.read_bytes()
    guard=RestartGuard(**{'expected_'+component+'_digest':'0'*64})
    with pytest.raises(RestartBlockedError):runtime.save(p,guard=guard)
    assert p.read_bytes()==before

def test_reordered_replay_fails_without_modifying_inputs():
    baseline=Atlas('v',state={'x':0});events=[Event(1,'set',{'state_patch':{'set':{'x':1}}}),Event(2,'set',{'state_patch':{'set':{'x':2}}})]
    before=atlas_to_dict(baseline)
    with pytest.raises(ValidationError):replay_declared_events(baseline,list(reversed(events)))
    assert atlas_to_dict(baseline)==before and events[0].payload['state_patch']['set']['x']==1

def test_schema_acceptance_does_not_establish_snapshot_digest_truth():
    d=json.loads((ROOT/'fixtures/valid.json').read_text())['state-snapshot'];d['topology_digest']='0'*64
    validate_contract('state-snapshot',d)
    # No standalone snapshot importer/verifier is implemented. Correct format is not hash truth.
    assert d['topology_digest']=='0'*64

def test_final_document_state_cannot_be_authenticated_from_events_without_baseline():
    d=fixture();d['state']['mode']='unrelated-final-state'
    a=atlas_from_dict(d)
    # Loading preserves a supplied final state; it does not infer an absent baseline.
    assert a.state['mode']=='unrelated-final-state'

@pytest.mark.parametrize('raw',[b'{"nested":{"x":1,"x":2}}',b'{"x":NaN}',b'{"x":Infinity}',b'{"x":-Infinity}',b'{',b'\xff'])
def test_strict_decoder_rejects_ambiguous_nonfinite_and_malformed_input(raw):
    from atomic_atlas_core.strict_json import loads_strict_json
    with pytest.raises(ValidationError):loads_strict_json(raw)

def test_finite_canonical_hashes_preserve_previous_byte_contract():
    import hashlib
    from atomic_atlas_core.provenance import canonical_json_bytes
    value={'text':'neutral π','n':1.0,'flag':False,'items':[None,2]}
    old_bytes=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    assert canonical_json_bytes(value)==old_bytes
    assert sha256_json(value)==hashlib.sha256(old_bytes).hexdigest()

def test_existing_finite_ledger_envelopes_still_verify(tmp_path):
    p=tmp_path/'historical.jsonl';env={'sequence':1,'previous_head':'0'*64,'record':{'fixture':'finite payload'}}
    head=sha256_json(env);p.write_text(json.dumps(dict(env,head=head))+'\n')
    l=JsonlHashLedger(p);assert l.count==1 and l.head==head
    l.append({'next':2});assert JsonlHashLedger(p).count==2
