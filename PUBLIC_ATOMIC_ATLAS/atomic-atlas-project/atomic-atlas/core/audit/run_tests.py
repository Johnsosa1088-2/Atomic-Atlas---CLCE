"""Execute original test functions using a bounded raises/tmp_path adapter.
This is NOT pytest. Original tests are unchanged; hardening tests are added. Unsupported fixture use fails.
"""
import importlib.util,pathlib,sys,tempfile,types,json
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
class Raises:
 def __init__(self,exception):self.exception=exception
 def __enter__(self):return self
 def __exit__(self,t,v,tb):
  if t is None:raise AssertionError('Expected '+self.exception.__name__)
  if not issubclass(t,self.exception):return False
  return True
shim=types.ModuleType('pytest');shim.raises=Raises;sys.modules['pytest']=shim
import inspect
results=[];skipped_files=[]
for p in sorted((ROOT/'tests').glob('test_*.py')):
 if p.name in {'test_adversarial_release.py','test_step7_boundaries.py'}:
  skipped_files.append({'file':p.name,'reason':'parameterized release tests require real pytest; run python -m pytest -q'})
  continue
 spec=importlib.util.spec_from_file_location(p.stem,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 for name,fn in inspect.getmembers(m,inspect.isfunction):
  if not name.startswith('test_'):continue
  try:
   parameters=list(inspect.signature(fn).parameters)
   assert parameters in [[],['tmp_path']],'Unsupported fixture'
   with tempfile.TemporaryDirectory() as tmp:fn(**({'tmp_path':pathlib.Path(tmp)} if parameters else {}))
   results.append({'test':name,'result':'PASS'})
  except Exception as e:results.append({'test':name,'result':'FAIL','error':repr(e)})
report={'runner':'stdlib compatibility harness; NOT pytest','passed':sum(r['result']=='PASS' for r in results),'failed':sum(r['result']=='FAIL' for r in results),'skipped_files':skipped_files,'results':results}
(ROOT/'audit/TEST_RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='results'}))
if report['failed']:raise SystemExit(1)
