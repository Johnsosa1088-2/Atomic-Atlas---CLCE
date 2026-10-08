import json,pathlib,sys,tempfile,threading,unittest,urllib.request,urllib.error
from http.server import ThreadingHTTPServer
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import server

class HTTPTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=pathlib.Path(self.tmp.name)/'events.sqlite';server.init(self.db)
  self.http=ThreadingHTTPServer(('127.0.0.1',0),server.make_handler(self.db,0))
  self.port=self.http.server_address[1];self.http.RequestHandlerClass=server.make_handler(self.db,self.port)
  self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
  self.url='http://127.0.0.1:'+str(self.port)
 def tearDown(self):
  self.http.shutdown();self.http.server_close();self.thread.join();self.tmp.cleanup()
 def post(self,origin=None):
  headers={'Content-Type':'application/json'}
  if origin:headers['Origin']=origin
  request=urllib.request.Request(self.url+'/api/events',
   data=json.dumps({'type':'retrieval_trace','payload':{'query':'fixture','method':'atlas'}}).encode(),headers=headers)
  return urllib.request.urlopen(request)
 def test_real_http_trace_is_persistent_and_exportable(self):
  with self.post(self.url) as response:
   self.assertEqual(response.status,201);saved=json.load(response)
  with urllib.request.urlopen(self.url+'/api/export') as response:export=json.load(response)
  self.assertEqual(export['anchor']['event_count'],1)
  self.assertEqual(export['events'][0]['sha256'],saved['sha256'])
  self.assertEqual(server.verify(self.db)['event_count'],1)
 def test_cross_origin_write_is_rejected(self):
  with self.assertRaises(urllib.error.HTTPError) as err:self.post('https://unrelated.invalid')
  self.assertEqual(err.exception.code,403);self.assertEqual(server.verify(self.db)['event_count'],0)
 def test_database_file_is_not_exposed_as_a_route(self):
  with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(self.url+'/neutral_provenance.sqlite')
  self.assertEqual(err.exception.code,404)
 def test_served_page_matches_standalone_bytes(self):
  with urllib.request.urlopen(self.url) as response:
   self.assertEqual(response.read(),(ROOT/'index.html').read_bytes())
  with urllib.request.urlopen(self.url+'/api/status') as response:status=json.load(response)
  self.assertEqual(status['storage'],'SQLite');self.assertTrue(status['verified'])

if __name__=='__main__':unittest.main()
