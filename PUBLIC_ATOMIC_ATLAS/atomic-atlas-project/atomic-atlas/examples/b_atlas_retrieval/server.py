"""Private loopback server; append-only SQLite provenance for the retrieval demonstration."""
import argparse,datetime,hashlib,json,pathlib,sqlite3,threading
from contextlib import contextmanager
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit
ROOT=pathlib.Path(__file__).resolve().parent
LOCK=threading.Lock()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()
@contextmanager
def connect(path):
 c=sqlite3.connect(path,timeout=10)
 try:
  c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA synchronous=FULL')
  with c:
   yield c
 finally:
  c.close()
def init(path):
 data=json.loads((ROOT/'data.json').read_text(encoding='utf-8'))
 with connect(path) as c:
  c.executescript("""
    CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,payload TEXT NOT NULL,sha256 TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,payload TEXT NOT NULL,previous_sha256 TEXT NOT NULL,sha256 TEXT NOT NULL);
    CREATE TRIGGER IF NOT EXISTS documents_no_update BEFORE UPDATE ON documents BEGIN SELECT RAISE(ABORT,'append-only documents'); END;
    CREATE TRIGGER IF NOT EXISTS documents_no_delete BEFORE DELETE ON documents BEGIN SELECT RAISE(ABORT,'append-only documents'); END;
    CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append-only events'); END;
    CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append-only events'); END;
  """)
  for doc in data['docs']:
   raw=canonical(doc);saved=c.execute('SELECT sha256 FROM documents WHERE id=?',(doc['id'],)).fetchone()
   if saved and saved[0]!=digest(raw):raise ValueError('Changed document requires a new version/ID: '+doc['id'])
   if not saved:c.execute('INSERT INTO documents VALUES(?,?,?)',(doc['id'],raw,digest(raw)))
 return data
def verify(path):
 head='0'*64;count=0
 with connect(path) as c:
  for seq,raw,prev,h in c.execute('SELECT seq,payload,previous_sha256,sha256 FROM events ORDER BY seq'):
   if seq!=count+1 or prev!=head or digest(canonical({'seq':seq,'payload':json.loads(raw),'previous_sha256':prev}))!=h:
    raise ValueError('Event hash chain mismatch')
   head=h;count+=1
  for ident,raw,h in c.execute('SELECT id,payload,sha256 FROM documents'):
   if digest(raw)!=h:raise ValueError('Document digest mismatch: '+ident)
 return {'event_count':count,'head_sha256':head,'verified':True}
def append(path,event):
 # Browser-submitted model answers/reviews are reported evidence, not independently verified claims.
 if event.get('type') not in {'retrieval_trace','model_answer','human_review'}:raise ValueError('Unsupported event type')
 if not isinstance(event.get('payload'),dict):raise ValueError('Payload must be an object')
 value={'type':event['type'],'payload':event['payload'],'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'source_class':'BROWSER_REPORTED_UNVERIFIED','scientific_validity_tested':False}
 with LOCK:
  verify(path)
  with connect(path) as c:
   c.execute('BEGIN IMMEDIATE')
   old=c.execute('SELECT seq,sha256 FROM events ORDER BY seq DESC LIMIT 1').fetchone()
   seq=old[0]+1 if old else 1;prev=old[1] if old else '0'*64
   h=digest(canonical({'seq':seq,'payload':value,'previous_sha256':prev}))
   c.execute('INSERT INTO events VALUES(?,?,?,?)',(seq,canonical(value),prev,h))
 return {'sequence':seq,'sha256':h,'recorded_at':value['recorded_at']}
def make_handler(path,port):
 class Handler(BaseHTTPRequestHandler):
  def json(self,status,value):
   raw=json.dumps(value,ensure_ascii=False).encode()
   self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8')
   self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def acceptable_host(self):
   return self.headers.get('Host') in {'127.0.0.1:'+str(port),'localhost:'+str(port)}
  def do_GET(self):
   if not self.acceptable_host():return self.json(403,{'error':'Loopback host required'})
   route=urlsplit(self.path).path
   if route=='/api/status':return self.json(200,dict(verify(path),storage='SQLite'))
   if route=='/api/export':
    with connect(path) as c:
     events=[{'sequence':s,'event':json.loads(v),'previous_sha256':p,'sha256':h}
       for s,v,p,h in c.execute('SELECT * FROM events ORDER BY seq')]
    return self.json(200,{'events':events,'anchor':verify(path)})
   allowed={'/':'index.html','/index.html':'index.html','/data.json':'data.json','/sources/specification.json':'sources/specification.json'}
   if route not in allowed:return self.json(404,{'error':'Unknown route'})
   f=ROOT/allowed[route];raw=f.read_bytes()
   mime='image/png' if f.suffix=='.png' else 'application/json' if f.suffix=='.json' else 'text/html; charset=utf-8'
   self.send_response(200);self.send_header('Content-Type',mime);self.send_header('X-Content-Type-Options','nosniff')
   self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def do_POST(self):
   if not self.acceptable_host():return self.json(403,{'error':'Loopback host required'})
   origin=self.headers.get('Origin')
   if origin not in {None,'http://127.0.0.1:'+str(port),'http://localhost:'+str(port)}:
    return self.json(403,{'error':'Same-origin request required'})
   if urlsplit(self.path).path!='/api/events':return self.json(404,{'error':'Unknown route'})
   if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.json(415,{'error':'JSON required'})
   try:
    size=int(self.headers.get('Content-Length','0'))
    if not 0<size<=100000:raise ValueError('Invalid request size')
    event=json.loads(self.rfile.read(size))
    return self.json(201,append(path,event))
   except (ValueError,TypeError,AttributeError) as e:return self.json(400,{'error':str(e)})
  def log_message(self,*args):pass
 return Handler
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765)
 parser.add_argument('--db',type=pathlib.Path,default=ROOT/'neutral_provenance.sqlite')
 parser.add_argument('--verify',action='store_true');args=parser.parse_args()
 init(args.db)
 if args.verify:print(json.dumps(verify(args.db)));return
 http=ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(args.db,args.port))
 print('Open http://127.0.0.1:'+str(args.port)+' — SQLite provenance is active.',flush=True)
 try:http.serve_forever()
 except KeyboardInterrupt:pass
 finally:http.server_close()
if __name__=='__main__':main()
