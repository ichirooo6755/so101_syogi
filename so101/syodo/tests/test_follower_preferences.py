import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

root = Path(__file__).parents[1]
sys.path.insert(0, str(root / 'scripts'))
spec = importlib.util.spec_from_file_location('pref_test_pad', root / 'scripts/follower_pad.py')
pad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pad)

class PreferencesTest(unittest.TestCase):
    def test_persist_and_validate(self):
        with tempfile.TemporaryDirectory() as directory:
            original = pad.PREFERENCES
            pad.PREFERENCES = Path(directory) / 'prefs.json'
            try:
                c = pad.Controller()
                self.assertEqual(c.preferences, {'speed':20, 'mirror':False})
                c.post({'kind':'preferences', 'speed':30, 'mirror':True})
                self.assertEqual(pad.load_preferences(), {'speed':30, 'mirror':True})
                c.armed = True
                with self.assertRaises(ValueError):
                    c.post({'kind':'preferences', 'speed':20, 'mirror':False})
                self.assertEqual(pad.load_preferences(), {'speed':30, 'mirror':True})
                with self.assertRaises(ValueError):
                    c.post({'kind':'preferences', 'speed':99, 'mirror':True})
            finally:
                pad.PREFERENCES = original

if __name__ == '__main__': unittest.main()
