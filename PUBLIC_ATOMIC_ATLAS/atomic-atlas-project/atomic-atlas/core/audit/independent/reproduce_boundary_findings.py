"""Run in a separate process against core/ of candidate 004 or 005; no input mutation."""
from pathlib import Path
import sys,json,tempfile
core=Path(sys.argv[1]).resolve();sys.path.insert(0,str(core/'src'))
from atomic_atlas_core import Atlas,AtlasRuntime,JsonlHashLedger
from atomic_atlas_core.errors import ValidationError
results=[]
with tempfile.TemporaryDirectory() as tmp:
 base=Path(tmp)
 for name in ['extra-envelope-field','missing-record','duplicate-document-key','duplicate-ledger-key','nan-payload','infinite-payload','negative-infinite-payload']:
  p=base/(name+'.jsonl')
  if name=='duplicate-document-key':
   raw=json.dumps(AtlasRuntime(Atlas('v')).document()).replace('"version": "v"','"version": "hidden", "version": "v"');p.write_text(raw)
   action=lambda:AtlasRuntime.load(p)
  elif name in ['nan-payload','infinite-payload','negative-infinite-payload']:
   ledger=JsonlHashLedger(p);number={'nan-payload':float('nan'),'infinite-payload':float('inf'),'negative-infinite-payload':float('-inf')}[name]
   action=lambda:ledger.append({'n':number})
  else:
   ledger=JsonlHashLedger(p);ledger.append(None if name=='missing-record' else {'x':1})
   raw=p.read_text();r=json.loads(raw)
   if name=='extra-envelope-field':r['unhashed_claim']='approved';raw=json.dumps(r)+'\n'
   elif name=='missing-record':del r['record'];raw=json.dumps(r)+'\n'
   else:raw=raw.replace('"record":','"record":{"hidden":1},"record":')
   p.write_text(raw);action=lambda:JsonlHashLedger(p)
  try:action();result='ACCEPTED'
  except ValidationError:result='REJECTED'
  results.append({'case':name,'observed':result})
print(json.dumps({'results':results},indent=2))
