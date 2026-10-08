"""Exercise the freeze checker with Windows-form relative paths and mutations."""
import pathlib,runpy,shutil,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name)/'project'
        shutil.copytree(ROOT,self.root,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache'))
    def run_checker(self,windows=False):
        checker=self.root/'step8/check_source_freeze.py'
        if windows:
            original=pathlib.Path.relative_to
            def relative(path,*args):
                return pathlib.PureWindowsPath(original(path,*args))
            with patch.object(pathlib.Path,'relative_to',relative):runpy.run_path(str(checker))
        else:runpy.run_path(str(checker))
    def test_windows_relative_paths_pass(self):self.run_checker(True)
    def test_posix_paths_pass(self):self.run_checker()
    def test_changed_frozen_file_rejected(self):
        with (self.root/'core/pyproject.toml').open('a') as f:f.write('\n# changed\n')
        with self.assertRaises(AssertionError):self.run_checker(True)
    def test_extra_frozen_file_rejected(self):
        (self.root/'core/src/unexpected.py').write_text('# extra')
        with self.assertRaises(AssertionError):self.run_checker(True)
    def test_missing_frozen_file_rejected(self):
        (self.root/'core/pyproject.toml').unlink()
        with self.assertRaises(FileNotFoundError):self.run_checker(True)
if __name__=='__main__':unittest.main()
