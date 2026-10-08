import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from atlas_store import Store

class Tests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = str(Path(self.directory.name)/'state.sqlite')
        self.store = Store(self.path)
        self.source = {'locator': 'synthetic:test', 'evidence': 'synthetic'}
    def tearDown(self):
        self.store.close()
        self.directory.cleanup()
    def add(self, identifier='a', state=None, head=None):
        return self.store.append(identifier, 'lamp', state or {'enabled': True}, self.source, head)
    def test_fresh_process(self):
        self.add()
        expected=self.store.recover('lamp')
        got=json.loads(subprocess.check_output([sys.executable,'demo.py','recover',self.path],text=True))
        self.assertEqual(expected,got)
    def test_replay_order(self):
        h=self.add();self.add('b',{'enabled':False},h)
        self.assertFalse(self.store.recover('lamp')['state']['enabled'])
        self.assertEqual(len(self.store.export()),2)
    def test_duplicate(self):
        h=self.add();self.assertEqual(self.add(),h);self.assertEqual(len(self.store.export()),1)
    def test_conflicting_id(self):
        self.add()
        with self.assertRaises(ValueError):self.add(state={'enabled':False})
    def test_stale_writer(self):
        self.add()
        other=Store(self.path)
        try:
            with self.assertRaises(ValueError):other.append('b','lamp',{},self.source,None)
        finally:other.close()
    def test_append_only(self):
        self.add()
        for statement in ('DELETE FROM records','UPDATE records SET body=body'):
            with self.assertRaises(sqlite3.IntegrityError):self.store.db.execute(statement)
    def test_tamper_detected(self):
        self.add();self.store.db.execute('DROP TRIGGER block_update')
        self.store.db.execute("UPDATE records SET body=replace(body,'true','false')")
        with self.assertRaises(ValueError):self.store.recover('lamp')
    def test_unknown_version(self):
        self.store.db.execute('PRAGMA user_version=99')
        with self.assertRaises(ValueError):Store(self.path)
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):self.add(state={'value':float('nan')})
        self.assertEqual(self.store.export(),[])
    def test_missing_source(self):
        with self.assertRaises(ValueError):self.store.append('a','lamp',{}, {},None)
    def test_hypothesis_preserved(self):
        source={'locator':'synthetic:hypothesis','evidence':'hypothesis'}
        self.store.append('a','lamp',{'claim':'untested'},source,None)
        self.assertEqual(self.store.recover('lamp')['source']['evidence'],'hypothesis')
    def test_unknown_entity(self):
        self.add();self.assertIsNone(self.store.recover('other'))

if __name__ == '__main__':unittest.main()
