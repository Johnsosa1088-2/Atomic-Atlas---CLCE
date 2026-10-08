import importlib.util,json,pathlib,shutil,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('inventory',ROOT/'step10/check_inventory.py')
inventory=importlib.util.module_from_spec(spec);spec.loader.exec_module(inventory)
class InventoryTests(unittest.TestCase):
    def test_windows_relative_path_uses_manifest_separator(self):
        self.assertEqual(pathlib.PureWindowsPath('core/LICENSE').as_posix(),'core/LICENSE')
    def test_venv_named_without_dot_is_not_silently_hidden(self):
        folder=self.root/'core'/'venv';folder.mkdir()
        (folder/'pyvenv.cfg').write_text('test environment')
        with self.assertRaises(ValueError):inventory.check(self.root)
    def test_project_log_is_rejected(self):
        (self.root/'windows-test-output.txt').write_text('test log')
        with self.assertRaises(ValueError):inventory.check(self.root)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)/'candidate'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    def test_unchanged_candidate_passes(self):
        self.assertEqual(inventory.check(self.root)['status'],'PASS')
    def test_unlisted_file_rejected(self):
        (self.root/'unexpected.txt').write_text('extra')
        with self.assertRaises(ValueError):inventory.check(self.root)
    def test_missing_file_rejected(self):
        (self.root/'AI_GUIDE.md').unlink()
        with self.assertRaises(ValueError):inventory.check(self.root)
    def test_changed_file_rejected(self):
        (self.root/'AI_GUIDE.md').write_text('changed')
        with self.assertRaises(ValueError):inventory.check(self.root)
if __name__=='__main__':unittest.main()
