import hashlib,json,pathlib,sqlite3,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import server

class ProvenanceTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.temp.name)/'provenance.sqlite'
  server.init(self.path)
 def tearDown(self):self.temp.cleanup()
 def test_connection_closes_after_success(self):
  with server.connect(self.path) as c:c.execute('SELECT 1')
  with self.assertRaises(sqlite3.ProgrammingError):c.execute('SELECT 1')
 def test_connection_closes_and_rolls_back_after_exception(self):
  with self.assertRaisesRegex(RuntimeError,'rollback fixture'):
   with server.connect(self.path) as c:
    c.execute('INSERT INTO events VALUES(1,?,?,?)',('{}','0'*64,'test'))
    raise RuntimeError('rollback fixture')
  with self.assertRaises(sqlite3.ProgrammingError):c.execute('SELECT 1')
  self.assertEqual(server.verify(self.path)['event_count'],0)
 def test_database_can_be_removed_after_init(self):
  self.path.unlink()
  self.assertFalse(self.path.exists())
 def test_source_hashes_match_actual_bytes(self):
  data=json.loads((ROOT/'data.json').read_text(encoding='utf-8'))
  for doc in data['docs']:
   source=doc['source'];p=ROOT/source['path']
   self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),source['sha256'],doc['id'])
 def test_synthetic_corpus_has_no_private_source_links(self):
  data=json.loads((ROOT/'data.json').read_text())
  self.assertNotIn('parent_ledger',data)
  for doc in data['docs']:
   self.assertEqual(doc['basis'],'SYNTHETIC_DEMO_SPECIFICATION')
   self.assertEqual(doc['source']['path'],'sources/specification.json')
   self.assertIsNone(doc['source']['date'])
 def test_restart_preserves_event_and_hash_anchor(self):
  saved=server.append(self.path,{'type':'retrieval_trace','payload':{'query':'test','method':'atlas','document_ids':['R-CONTROL']}})
  server.init(self.path);receipt=server.verify(self.path)
  self.assertEqual(receipt['event_count'],1);self.assertEqual(receipt['head_sha256'],saved['sha256'])
  with server.connect(self.path) as c:
   row=json.loads(c.execute('SELECT payload FROM events').fetchone()[0])
  self.assertEqual(row['source_class'],'BROWSER_REPORTED_UNVERIFIED')
  self.assertFalse(row['scientific_validity_tested'])
 def test_sql_rejects_event_update_and_delete(self):
  server.append(self.path,{'type':'model_answer','payload':{'answer':'reported'}})
  for sql in ["UPDATE events SET payload='changed'","DELETE FROM events"]:
   with self.assertRaises(sqlite3.DatabaseError):
    with server.connect(self.path) as c:c.execute(sql)
  self.assertEqual(server.verify(self.path)['event_count'],1)
 def test_sql_rejects_source_update_and_delete(self):
  for sql in ["UPDATE documents SET payload='changed'","DELETE FROM documents"]:
   with self.assertRaises(sqlite3.DatabaseError):
    with server.connect(self.path) as c:c.execute(sql)
 def test_repeated_source_import_is_idempotent(self):
  server.init(self.path)
  with server.connect(self.path) as c:
   self.assertEqual(c.execute('SELECT count(*) FROM documents').fetchone()[0],12)
 def test_hash_verifier_detects_tampering_even_without_triggers(self):
  server.append(self.path,{'type':'retrieval_trace','payload':{'query':'test'}})
  with server.connect(self.path) as c:
   c.execute('DROP TRIGGER events_no_update');c.execute("UPDATE events SET payload='{}'")
  with self.assertRaisesRegex(ValueError,'chain'):server.verify(self.path)
 def test_unsupported_event_is_not_recorded(self):
  with self.assertRaises(ValueError):server.append(self.path,{'type':'scientific_proof','payload':{}})
  self.assertEqual(server.verify(self.path)['event_count'],0)

if __name__=='__main__':unittest.main()
