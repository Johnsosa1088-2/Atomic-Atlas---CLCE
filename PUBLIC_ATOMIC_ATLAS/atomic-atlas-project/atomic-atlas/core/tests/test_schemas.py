import copy,json,pathlib,math
from dataclasses import asdict
import pytest
from atomic_atlas_core import *
from atomic_atlas_core.errors import ValidationError
ROOT=pathlib.Path(__file__).resolve().parents[1]

def test_all_valid_fixtures():
 for name,value in json.loads((ROOT/'fixtures/valid.json').read_text()).items():validate_contract(name,value)

def test_invalid_fixture_classification_and_model_rejection():
 for item in json.loads((ROOT/'fixtures/invalid.json').read_text()):
  if item['structural_result']=='REJECT':
   with pytest.raises(ValidationError):validate_contract(item['schema'],item['value'])
  else:
   validate_contract(item['schema'],item['value'])
   with pytest.raises(ValidationError):
    if item['schema']=='build-spec':build_atlas(item['value'])
    else:atlas_from_dict(item['value'])

def test_nonfinite_and_nonjson_values_rejected():
 for bad in [float('nan'),float('inf'),object(),{1:'nonstring key'}]:
  with pytest.raises(ValidationError):build_atlas({'schema':'ATLAS_BUILD_SPEC/0.1','version':'v','initial_state':{'bad':bad}})

def test_runtime_rejects_invalid_patch_without_mutation():
 runtime=AtlasRuntime(Atlas('v',state={'x':0}))
 with pytest.raises(ValidationError):runtime.apply_state_event(event_type='set',set_values={'x':float('nan')})
 assert runtime.atlas.state=={'x':0} and runtime.atlas.events==[]

def test_two_domains_use_unchanged_build_schema_and_replay():
 for ids in [('tank','valve'),('gear','axle')]:
  spec={'schema':'ATLAS_BUILD_SPEC/0.1','version':'v','entities':[{'id':i} for i in ids],'relations':[{'source':ids[0],'target':ids[1],'type':'declared_connection'}],'initial_state':{'status':'idle'}}
  baseline=build_atlas(spec);runtime=AtlasRuntime(atlas_from_dict(atlas_to_dict(baseline)))
  runtime.apply_state_event(event_type='declared',set_values={'status':'active'})
  validate_contract('document',runtime.document());validate_contract('topology',runtime.atlas.topology_payload());validate_contract('state-snapshot',asdict(runtime.atlas.snapshot()))
  assert replay_declared_events(baseline,runtime.atlas.events).state_digest()==runtime.atlas.state_digest()

def test_schema_copies_are_identical():
 for p in (ROOT/'schemas').glob('*.json'):assert p.read_bytes()==(ROOT/'src/atomic_atlas_core/schemas'/p.name).read_bytes()

def test_dictionary_key_mismatch_is_semantic_error():
 a=Atlas('v');a.add_entity(Entity('a'));a.add_entity(Entity('b'));a.entities={'a':a.entities['b'],'b':a.entities['a']}
 validate_contract('topology',a.topology_payload())
 with pytest.raises(ValidationError):a.validate_integrity()

def test_subset_validator_rejects_unsupported_schema_keywords():
 from atomic_atlas_core.validation import _schema_check
 with pytest.raises(ValidationError):_schema_check({'oneOf':[]})

def test_missing_coordinate_and_measurement_remain_unknown():
 value={'id':'e','coordinates':{'x':None,'y':None}};before=copy.deepcopy(value);validate_contract('entity',value);assert value==before


def test_unsupported_replay_scope_rejected():
 with pytest.raises(ValidationError):AtlasRuntime(Atlas('v')).replay_manifest('FULL_DYNAMIC_REPLAY')
