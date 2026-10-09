import unittest,json,copy,tempfile
from pathlib import Path
from adapter import validate,commit,pressure_work_J,balance_residual_J
from atlas_store import Store
from bridge import packet

class AdapterTests(unittest.TestCase):
    def setUp(self): self.data=json.loads(Path('scaffold.json').read_text())
    def test_unknowns_stay_unknown(self):
        validate(self.data);self.assertIsNone(balance_residual_J(self.data['energy']))
        self.assertTrue(all(p['water_volume_m3'] is None for p in self.data['pockets']))
    def test_connected_legs(self):
        by={p['id']:p for p in self.data['parts']}
        for side in ('left','right'):
            self.assertEqual(by[f'aurelia.part.{side}_thigh']['parent'],'aurelia.part.pelvis')
    def test_bad_graphs(self):
        for mode in ('cycle','dangling','duplicate'):
            d=copy.deepcopy(self.data)
            if mode=='cycle':d['parts'][0]['parent']=d['parts'][1]['id']
            if mode=='dangling':d['parts'][1]['parent']='absent'
            if mode=='duplicate':d['parts'].append(d['parts'][0])
            with self.assertRaises(ValueError):validate(d)
    def test_bad_pocket(self):
        for value in (-1,float('nan'),True):
            d=copy.deepcopy(self.data);d['pockets'][0]['water_volume_m3']=value
            with self.assertRaises(ValueError):validate(d)
    def test_known_work_and_balance(self):
        self.assertAlmostEqual(pressure_work_J(1000,.002),2)
        self.assertEqual(balance_residual_J({'input_J':10,'mechanical_output_J':3,'heat_loss_J':2,'stored_change_J':5}),0)
    def test_append_recover_deduplicate_and_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=str(Path(tmp)/'test.sqlite');a=commit(self.data,path);self.assertEqual(commit(self.data,path),a)
            changed=copy.deepcopy(self.data);changed['parts'][0]['anchor']['xy'][0]+=1
            b=commit(changed,path);self.assertNotEqual(a,b)
            s=Store(path);self.assertEqual(len(s.export()),2);self.assertEqual(s.recover('aurelia.cage.scaffold')['state'],changed);s.close()
            self.assertTrue(packet(path,'aurelia cage')['records'])
    def test_reject_before_database_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'absent.sqlite';self.data['parts'][1]['parent']='missing'
            with self.assertRaises(ValueError):commit(self.data,str(path))
            self.assertFalse(path.exists())

if __name__=='__main__':unittest.main()
