import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import verify_guarded_resumed_r2 as v,verify_guarded_completion_r2 as completion,json
@unittest.skipUnless((v.ROOT/'work/evidence/b006-connected-resumed-campaign.json').exists(), 'Private completed Pocket trial required')
class Tests(unittest.TestCase):
 def test_actual_completed_raw_trial_replays(self):
  proof=v.verify('B006',publish=False);self.assertTrue(proof['pass']);self.assertEqual(proof['committed_saves'],325);self.assertEqual(proof['final_expected_files']['generation'],974)
  doc=json.loads((v.ROOT/'work/evidence/b006-connected-resumed-campaign.json').read_text());self.assertTrue(completion.check(doc,proof))
 def test_foreign_build_refused(self):
  with self.assertRaises(ValueError):v.verify('B005',publish=False)
 def test_changed_baseline_hash_refused(self):
  with patch.object(v,'sha',return_value='changed'),self.assertRaises(ValueError):v.verify('B006',publish=False)
if __name__=='__main__':unittest.main()
