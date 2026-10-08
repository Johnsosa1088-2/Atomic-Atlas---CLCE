"""Offline validation of the schema subset used by this package.

Not a general Draft 2020-12 validator. Schemas remain standard JSON Schema for
independent validators; this evaluator rejects unsupported schema keywords and
never resolves remote references. Cross-object integrity remains model validation.
"""
import json,math,re
from functools import lru_cache
from pathlib import Path
from .errors import ValidationError
SUPPORTED={'$schema','$id','title','description','$ref','$defs','type','properties','required','additionalProperties','propertyNames','items','uniqueItems','minItems','minLength','pattern','minimum','const','enum','anyOf'}

def _schema_check(s):
 if not isinstance(s,dict):raise ValidationError('schema must be an object')
 unknown=set(s)-SUPPORTED
 if unknown:raise ValidationError('unsupported schema keywords: '+str(sorted(unknown)))
 for key in ('$defs','properties'):
  for child in s.get(key,{}).values():_schema_check(child)
 for key in ('items','propertyNames','additionalProperties'):
  if isinstance(s.get(key),dict):_schema_check(s[key])
 for child in s.get('anyOf',[]):_schema_check(child)

@lru_cache(maxsize=32)
def _load(name):
 if name not in {'build-spec','document','topology','entity','relation','candidate-overlay','observation','state-snapshot','replay-manifest','neutral-profile','event','provenance'}:
  raise ValidationError('unknown schema name')
 schema=json.loads((Path(__file__).parent/'schemas'/(name+'.schema.json')).read_text(encoding='utf-8'))
 _schema_check(schema)
 return schema

def _json_values(value,path='$'):
 if value is None or type(value) in (str,bool,int):return
 if type(value) is float:
  if not math.isfinite(value):raise ValidationError(path+': finite JSON numbers required')
  return
 if isinstance(value,(list,tuple)):
  for i,item in enumerate(value):_json_values(item,path+'/'+str(i))
  return
 if isinstance(value,dict):
  for key,item in value.items():
   if not isinstance(key,str):raise ValidationError(path+': JSON object keys must be strings')
   _json_values(item,path+'/'+key)
  return
 raise ValidationError(path+': unsupported non-JSON value')

def _is_type(value,kind):
 return {'null':value is None,'boolean':type(value) is bool,'string':isinstance(value,str),'number':type(value) in (int,float),'integer':type(value) is int or (type(value) is float and value.is_integer()),'object':isinstance(value,dict),'array':isinstance(value,(list,tuple))}.get(kind,False)

def _equal(a,b):
 if type(a) is bool or type(b) is bool:return type(a) is type(b) and a==b
 if isinstance(a,dict) and isinstance(b,dict):return set(a)==set(b) and all(_equal(a[k],b[k]) for k in a)
 if isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)):return len(a)==len(b) and all(_equal(x,y) for x,y in zip(a,b))
 return a==b

def _check(value,s,root,path):
 def fail(message):raise ValidationError(path+': '+message)
 if '$ref' in s:
  ref=s['$ref']
  if not ref.startswith('#/$defs/') or '/' in ref[len('#/$defs/'):]:fail('only local definition references supported')
  name=ref[len('#/$defs/'):]
  if name not in root.get('$defs',{}):fail('missing schema definition')
  _check(value,root['$defs'][name],root,path)
 if 'anyOf' in s:
  for branch in s['anyOf']:
   try:_check(value,branch,root,path);break
   except ValidationError:pass
  else:fail('no permitted schema branch matches')
 if 'type' in s:
  kinds=s['type'] if isinstance(s['type'],list) else [s['type']]
  if not any(_is_type(value,k) for k in kinds):fail('expected '+str(kinds))
 if 'const' in s and not _equal(value,s['const']):fail('incorrect constant')
 if 'enum' in s and not any(_equal(value,x) for x in s['enum']):fail('value outside declared enumeration')
 if isinstance(value,str):
  if len(value)<s.get('minLength',0):fail('string too short')
  if 'pattern' in s and re.search(s['pattern'],value) is None:fail('string does not match pattern')
 if type(value) in (int,float) and 'minimum' in s and value<s['minimum']:fail('number below minimum')
 if isinstance(value,(list,tuple)):
  if len(value)<s.get('minItems',0):fail('array too short')
  if s.get('uniqueItems') and any(_equal(value[i],value[j]) for i in range(len(value)) for j in range(i)):fail('duplicate array items')
  if 'items' in s:
   for i,item in enumerate(value):_check(item,s['items'],root,path+'/'+str(i))
 if isinstance(value,dict):
  for key in s.get('required',[]):
   if key not in value:fail('missing field '+key)
  props=s.get('properties',{})
  for key,item in value.items():
   if 'propertyNames' in s:_check(key,s['propertyNames'],root,path+'/'+key)
   if key in props:_check(item,props[key],root,path+'/'+key)
   else:
    extra=s.get('additionalProperties',True)
    if extra is False:fail('unknown field '+key)
    if isinstance(extra,dict):_check(item,extra,root,path+'/'+key)

def validate_contract(name,value):
 """Validate finite JSON structure; return no coerced or default-filled value."""
 _json_values(value)
 schema=_load(name)
 _check(value,schema,schema,'$')
