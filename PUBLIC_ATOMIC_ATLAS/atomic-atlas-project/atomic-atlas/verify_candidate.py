"""Run verification in a retained external copy; preserve source hash anchors."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parent
def main():
 if not shutil.which('node'):
  print('Node.js unavailable. Install Node LTS, reopen terminal and check node --version.');return 2
 missing=[n for n in ['pytest','jsonschema'] if importlib.util.find_spec(n) is None]
 if missing:
  print('Missing dependencies: '+', '.join(missing)+'; install core/audit/independent/requirements-lock.txt using this Python.');return 2
 subprocess.run([sys.executable,str(ROOT/'step10/check_inventory.py')],check=True)
 run=Path(tempfile.mkdtemp(prefix='atlas-014-run-',dir=ROOT.parent));work=run/'project'
 print('Retained results: '+str(run),flush=True)
 shutil.copytree(ROOT,work,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','.venv'))
 code=1
 try:
  with (run/'test-output.txt').open('w',encoding='utf-8') as log:
   p=subprocess.Popen([sys.executable,str(work/'run_suite.py')],cwd=work,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
   for line in p.stdout:
    log.write(line);log.flush()
    try:print(line,end='',flush=True)
    except UnicodeEncodeError:print(line.encode('ascii','backslashreplace').decode(),end='',flush=True)
   code=p.wait()
 finally:
  intact=subprocess.run([sys.executable,str(ROOT/'step10/check_inventory.py')]).returncode==0
  if not intact:code=1
  (run/'RUN_RECEIPT.json').write_text(json.dumps({'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_manifest_sha256':hashlib.sha256((ROOT/'RELEASE_MANIFEST.json').read_bytes()).hexdigest(),'suite_exit_code':code,'source_inventory_after_run_pass':intact,'python':sys.version,'platform':sys.platform,'status':'PASS' if code==0 else 'FAIL'},indent=2)+'\n',encoding='utf-8')
 print('PASS: full available suites passed; original package hashes preserved.' if code==0 else 'FAIL: see retained test-output.txt and RUN_RECEIPT.json.',flush=True)
 return code
if __name__=='__main__':sys.exit(main())
