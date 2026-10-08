"""Seed six prohibited promotions in temporary copies; the targeted tests must fail."""
from pathlib import Path
import tempfile,shutil,subprocess,sys,os,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=[
 ('connection_to_flow','core/src/atomic_atlas_core/analysis.py','transport_occurred: bool = False','transport_occurred: bool = True','core'),
 ('correlation_to_state','core/src/atomic_atlas_core/model.py','        self.observations.append(deepcopy(observation))','        self.state["causal_effect"] = True\n        self.observations.append(deepcopy(observation))','core'),
 ('label_to_mechanism','core/src/atomic_atlas_core/analysis.py','"physical_mechanism_established": False','"physical_mechanism_established": True','core'),
 ('candidate_to_validated','core/src/atomic_atlas_core/model.py','        self.candidate_overlays[overlay.id] = deepcopy(overlay)','        self.candidate_overlays[overlay.id] = deepcopy(overlay)\n        object.__setattr__(self.candidate_overlays[overlay.id], "status", "validated")','core'),
 ('replay_to_evidence','core/src/atomic_atlas_core/runtime.py','    return clone','    from .model import EvidenceReference\n    clone.record_observation(Observation("fabricated", {"claim":"replay proof"}, EvidenceReference("fabricated by replay", verified=True)))\n    return clone','core'),
 ('review_to_verified','proposal_harness/harness.py',"'truth_status':'ACCEPTED_DECLARATION'","'truth_status':'VERIFIED'",'harness')]

def run():
 results=[]
 original={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for _,name,_,_,_ in CONTROLS}
 for cid,name,needle,replacement,suite in CONTROLS:
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'project';p.mkdir()
   shutil.copytree(ROOT/'core',p/'core',ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','audit'))
   shutil.copytree(ROOT/'proposal_harness',p/'proposal_harness',ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','ALL_PROJECT_CHECKS.txt'))
   f=p/name;source=f.read_text();assert source.count(needle)==1,(cid,'mutation target is not unique');f.write_text(source.replace(needle,replacement,1))
   target=p/('core/tests/test_step7_boundaries.py' if suite=='core' else 'proposal_harness/tests/test_step7_claims.py')
   env=dict(os.environ,PYTHONPATH=str(p/'core/src'))
   child=subprocess.run([sys.executable,'-m','pytest',str(target),'-q'],cwd=p,env=env,text=True,capture_output=True)
   failed=re.search(r'(\d+) failed',child.stdout)
   assert child.returncode==1 and failed,(cid,child.stdout,child.stderr)
   results.append({'control':cid,'result':'DETECTED','failing_cases':int(failed.group(1)),'mutated_source':name,'scope':'temporary copy only'})
 assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in original.items())
 out={'result':'PASS','controls':results,'source_files_unchanged':True,'source_file_hashes':original,'limits':'These six seeded controls demonstrate targeted detection, not exhaustive mutation coverage or semantic truth recognition.'}
 (ROOT/'step7/MUTATION_RESULTS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':run()
