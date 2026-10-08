"""Step 7: derived capabilities never promote stored declarations into physical evidence."""
import copy
from dataclasses import asdict
import pytest
from atomic_atlas_core import *
from atomic_atlas_core.errors import ValidationError


def atlas():
    a=Atlas('boundary-v1',state={'mass':1,'energy':10});a.add_entity(Entity('a'));a.add_entity(Entity('b'));return a

@pytest.mark.parametrize('flags',[{}, {'transport_enabled':True}, {'state_mutation_enabled':True}, {'transport_enabled':True,'state_mutation_enabled':True}])
def test_connection_and_declared_flags_do_not_execute_flow(flags):
    a=atlas();a.add_relation(Relation('a','b','declared_connection',**flags));before=atlas_to_dict(a)
    trace=trace_route(['a','b'],a.relations)
    out=budget_preview(trace,quantities={'arbitrary_unit':{'input':10,'stored':4,'loss':6}},evidence_id='synthetic')
    assert trace.status=='REACHED_DECLARED_TARGET' and not trace.transport_occurred and not trace.state_changed
    assert not out['transport_enabled'] and not out['physical_mechanism_established'] and not out['evidence_verified']
    assert atlas_to_dict(a)==before

@pytest.mark.parametrize('type_label',['correlated_with','causes','PROVEN_CAUSAL_MECHANISM','Navier-Stokes transport','ordinary_link'])
def test_relation_label_does_not_infer_causality_or_mechanism(type_label):
    a=atlas();a.add_relation(Relation('a','b',type_label,attributes={'causality_established':True,'physical_mechanism_established':True}));before=atlas_to_dict(a)
    trace=trace_route(['a','b'],a.relations)
    out=budget_preview(trace,quantities={'declared_energy':{'input':10,'output':10}},evidence_id='caller-label')
    assert out['status']=='ARITHMETIC_CLOSED_HYPOTHESIS' and not out['physical_mechanism_established'] and not out['evidence_verified']
    assert not trace.state_changed and atlas_to_dict(a)==before
    # Input labels/attributes are preserved declarations, not a causal-analysis result.
    assert a.relations[0].attributes['causality_established'] is True

@pytest.mark.parametrize('verified',[False,True])
def test_correlated_observations_and_caller_verified_flag_do_not_change_state(verified):
    a=atlas();before=a.state_digest();r=AtlasRuntime(a)
    for i in range(3):r.record_observation(Observation('o'+str(i),{'x':i,'y':i,'claimed_causal':True},EvidenceReference('synthetic paired series',verified=verified)))
    assert a.state_digest()==before and not a.events
    assert all(o.evidence.verified is verified for o in a.observations)
    assert 'causal_effect' not in a.state

@pytest.mark.parametrize('status',['validated','VALIDATED','established','approved'])
def test_candidate_status_promotion_rejected_by_loader(status):
    a=atlas();a.add_candidate_overlay(CandidateOverlay('c',entities=(Entity('c1',candidate=True),)))
    d=atlas_to_dict(a);d['candidate_overlays'][0]['status']=status
    with pytest.raises(ValidationError):atlas_from_dict(d)
    assert a.candidate_overlays['c'].status=='candidate'

@pytest.mark.parametrize('flag',['transport_enabled','state_mutation_enabled'])
def test_candidate_cannot_enable_runtime_capabilities(flag):
    with pytest.raises(ValidationError):CandidateOverlay('c',entities=(Entity('c1',candidate=True),),relations=(Relation('a','c1','possible',candidate=True,**{flag:True}),))

def test_roundtrip_snapshot_save_load_never_promote_candidates(tmp_path):
    a=atlas();r=AtlasRuntime(a);before=a.state_digest()
    r.attach_candidate_overlay(CandidateOverlay('c',entities=(Entity('c1',candidate=True),),relations=(Relation('a','c1','possible',candidate=True),)))
    snap=a.snapshot();p=tmp_path/'state.json';r.save(p);loaded=AtlasRuntime.load(p)
    assert a.state_digest()==before and loaded.atlas.state_digest()==before
    assert 'c1' not in loaded.atlas.entities and 'candidate_overlays' not in snap.state
    assert trace_route(['a','c1'],loaded.atlas.candidate_overlays['c'].relations).status=='CUT'
    assert loaded.atlas.candidate_overlays['c'].status=='candidate'

def test_replay_recovers_a_false_declared_claim_without_proving_it():
    baseline=atlas();r=AtlasRuntime(atlas_from_dict(atlas_to_dict(baseline)))
    r.apply_state_event(event_type='caller_says_physics_passed',set_values={'claimed_measurement':999,'experiment_passed':True})
    out=replay_declared_events(baseline,r.atlas.events);manifest=asdict(r.replay_manifest())
    assert out.state==r.atlas.state and out.observations==[]
    assert manifest['scope']=='DECLARED_EVENT_REPLAY' and not manifest['full_dynamic_replay']
    assert 'evidence_verified' not in manifest
    # The deliberately unsupported claim can be recovered as data, never authenticated as an experiment.

def test_replay_does_not_create_evidence_references_or_observations():
    baseline=atlas();r=AtlasRuntime(atlas_from_dict(atlas_to_dict(baseline)))
    r.apply_state_event(event_type='declared',set_values={'x':1})
    out=replay_declared_events(baseline,r.atlas.events)
    assert not out.observations and out.events[0].evidence is None and not out.provenance
    assert baseline.events==[] and baseline.state=={'mass':1,'energy':10}

@pytest.mark.parametrize('quantities',[{},None,[],{'declared_unit':None},{'':{'input':1,'output':1}}])
def test_empty_or_malformed_budgets_cannot_claim_arithmetic_closure(quantities):
    trace=trace_route(['a','b'],[Relation('a','b','declared')])
    with pytest.raises(ValidationError):budget_preview(trace,quantities=quantities,evidence_id='fixture')

@pytest.mark.parametrize('bad',[{'input':10,'output':9},{'output':10,'input':10},{'input':float('nan'),'output':0}])
def test_failed_budget_never_mutates_established_state(bad):
    a=atlas();a.add_relation(Relation('a','b','declared'));before=atlas_to_dict(a)
    with pytest.raises(ValidationError):budget_preview(trace_route(['a','b'],a.relations),quantities={'declared_unit':bad},evidence_id='fixture')
    assert atlas_to_dict(a)==before

@pytest.mark.parametrize('label',['',False,1])
def test_nontext_or_empty_budget_bucket_labels_rejected(label):
    trace=trace_route(['a','b'],[Relation('a','b','declared')])
    with pytest.raises(ValidationError):budget_preview(trace,quantities={'declared_unit':{'input':1,label:1}},evidence_id='fixture')

def test_ambient_decimal_rounding_cannot_hide_budget_imbalance():
    from decimal import localcontext
    trace=trace_route(['a','b'],[Relation('a','b','declared')])
    with localcontext() as ctx:
        ctx.prec=4
        with pytest.raises(ValidationError):budget_preview(trace,quantities={'declared_unit':{'input':'100000','output':'99999'}},evidence_id='fixture')
        out=budget_preview(trace,quantities={'declared_unit':{'input':'100000','stored':'99999','loss':'1'}},evidence_id='fixture')
    assert out['status']=='ARITHMETIC_CLOSED_HYPOTHESIS' and not out['physical_mechanism_established']
