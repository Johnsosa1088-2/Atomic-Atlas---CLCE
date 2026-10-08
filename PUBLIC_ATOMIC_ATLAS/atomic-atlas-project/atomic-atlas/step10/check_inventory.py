"""Check exact distributable inventory, hashes and documentation references."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
def check(root=ROOT):
    manifest=json.loads((root/'RELEASE_MANIFEST.json').read_text())['files']
    actual={f.relative_to(root).as_posix() for f in root.rglob('*') if f.is_file() and not any(x in f.parts for x in ['__pycache__','.pytest_cache','.venv']) and f.name!='RELEASE_MANIFEST.json'}
    if actual!=set(manifest):raise ValueError('Inventory differs: extra='+str(sorted(actual-set(manifest)))+' missing='+str(sorted(set(manifest)-actual)))
    for name,digest in manifest.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Digest differs: '+name)
    references=0
    for name in ['HUMAN_GUIDE.md','AI_GUIDE.md','CAPABILITIES_AND_LIMITATIONS.md']:
        text=(root/name).read_text()
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if not (root/target).is_file():raise ValueError('Missing document link: '+target)
            references+=1
    register=json.loads((root/'step9/CAPABILITY_REGISTER.json').read_text())
    for claim in register['capabilities']:
        if not (root/claim['evidence']).is_file():raise ValueError('Missing evidence: '+claim['evidence'])
    if (root/'ATLAS_ASPIRATION_MAP_009.zip').exists():raise ValueError('Excluded archive present')
    return {'status':'PASS','inventoried_files':len(actual),'document_links':references,'capability_evidence_paths':len(register['capabilities'])}
if __name__=='__main__':print(json.dumps(check(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT)))
