"""Independent Draft 2020-12 and differential checks; finite JSON instances only."""
from pathlib import Path
import copy,hashlib,json,sys,platform,importlib.metadata as meta
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from atomic_atlas_core.validation import validate_contract
from atomic_atlas_core.errors import ValidationError
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry

def no_network(uri):
    raise RuntimeError('Remote reference resolution disabled: '+uri)

def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def paths(v,base=()):
    yield base,v
    if isinstance(v,dict):
        for k,item in v.items():yield from paths(item,base+(k,))
    elif isinstance(v,list):
        for k,item in enumerate(v):yield from paths(item,base+(k,))

def replace(v,path,new):
    if not path:return copy.deepcopy(new)
    out=copy.deepcopy(v);node=out
    for k in path[:-1]:node=node[k]
    node[path[-1]]=copy.deepcopy(new)
    return out

def run():
    schemas={f.name.removesuffix('.schema.json'):json.loads(f.read_text()) for f in sorted((ROOT/'schemas').glob('*.json'))}
    assert len(schemas)==12
    assert len({s['$id'] for s in schemas.values()})==12
    try:Draft202012Validator.check_schema({'type':'not-a-json-type'})
    except SchemaError:pass
    else:raise AssertionError('independent metaschema negative control failed')
    assert Draft202012Validator({'type':'integer'}).is_valid(1.0)
    assert not Draft202012Validator({'type':'integer'}).is_valid(True)
    validators={};schema_results=[]
    for name,schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema,registry=Registry(retrieve=no_network))
        refs=[]
        for path,value in paths(schema):
            if isinstance(value,dict) and '$ref' in value:
                ref=value['$ref'];validator._resolver.lookup(ref);refs.append({'path':list(path),'ref':ref})
        schema_results.append({'schema':name,'metaschema':'PASS','references_resolved':len(refs),'references':refs,'sha256':digest(schema)})
        validators[name]=validator
    valid=json.loads((ROOT/'fixtures/valid.json').read_text());invalid=json.loads((ROOT/'fixtures/invalid.json').read_text())
    cases=[{'schema':n,'label':'original valid fixture','expected':'PASS','value':v} for n,v in valid.items()]
    cases += [{'schema':i['schema'],'label':i['label'],'expected':i['structural_result'],'value':i['value']} for i in invalid]
    originals=len(cases)
    mutations=[None,False,True,0,1,1.0,-1,0.5,'',' ','x','0'*64,'g'*64,[],{},[False,0],[1,1.0]]
    for name,value in valid.items():
        for path,node in paths(value):
            for mutation in mutations:
                cases.append({'schema':name,'label':'replace '+json.dumps(list(path)),'value':replace(value,path,mutation)})
            if isinstance(node,dict):
                for key in node:
                    new=copy.deepcopy(node);del new[key]
                    cases.append({'schema':name,'label':'remove '+json.dumps(list(path)+( [key])),'value':replace(value,path,new)})
                new=copy.deepcopy(node);new['__unexpected__']=1
                cases.append({'schema':name,'label':'extra property '+json.dumps(list(path)),'value':replace(value,path,new)})
            elif isinstance(node,list) and node:
                cases.append({'schema':name,'label':'duplicate array entry '+json.dumps(list(path)),'value':replace(value,path,node+[node[0]])})
    seen=set();results=[];disagreements=[];expectation_failures=[]
    for index,c in enumerate(cases):
        anchor=digest({'schema':c['schema'],'value':c['value']})
        # Keep supplied fixtures even when content duplicates a prior original.
        if index>=originals and anchor in seen:continue
        seen.add(anchor)
        external_errors=list(validators[c['schema']].iter_errors(c['value']))
        independent='REJECT' if external_errors else 'PASS'
        try:validate_contract(c['schema'],copy.deepcopy(c['value']));bundled='PASS';message=None
        except ValidationError as exc:bundled='REJECT';message=str(exc)
        r={'schema':c['schema'],'label':c['label'],'value_sha256':digest(c['value']),'independent':independent,'bundled':bundled,'origin':'supplied_fixture' if index<originals else 'generated_mutation'}
        if 'expected' in c:r['expected']=c['expected']
        results.append(r)
        if independent!=bundled:
            disagreements.append({**r,'value':c['value'],'bundled_error':message,'independent_errors':[{'instance_path':list(e.absolute_path),'schema_path':list(e.absolute_schema_path),'message':e.message} for e in external_errors]})
        if 'expected' in c and independent!=c['expected']:expectation_failures.append({**r,'value':c['value']})
    out={'python':platform.python_version(),'platform':platform.platform(),'validator':'jsonschema.Draft202012Validator','versions':{n:meta.version(n) for n in ['jsonschema','jsonschema-specifications','referencing','rpds-py','attrs','pytest']},'schema_results':schema_results,'case_count':len(results),'supplied_fixture_count':originals,'generated_mutation_count':len(results)-originals,'classification_counts':dict(Counter(r['independent'] for r in results)),'by_schema':dict(Counter(r['schema'] for r in results)),'disagreements':disagreements,'expectation_failures':expectation_failures,'case_results':results,'limits':['Finite JSON domain only; Python tuples/nonfinite values are separate host API policy.','No exhaustive validator certification or scientific validation.','Private resolver lookup used only to audit all local references; validator version is pinned.','Generated mutations are bounded and correlated, not independent scientific trials.']}
    target=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'audit/independent/conformance_results.json'
    target.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:out[k] for k in ['case_count','supplied_fixture_count','generated_mutation_count','classification_counts','by_schema','disagreements','expectation_failures']},indent=2))
    return 1 if disagreements or expectation_failures else 0
if __name__=='__main__':raise SystemExit(run())
