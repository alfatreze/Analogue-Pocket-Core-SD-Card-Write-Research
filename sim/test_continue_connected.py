#!/usr/bin/env python3
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import continue_connected as c
class ContinueTests(unittest.TestCase):
 def setup_root(self,root,state):
  folder=root/'work/evidence';(folder/'jtag').mkdir(parents=True)
  (folder/'custom-build-audit-guarded06.json').write_text('{}')
  (folder/'b005-connected-campaign.json').write_text(json.dumps({'state':state}))
 def test_failed_baseline_never_programs(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);self.setup_root(root,'failed')
   with patch.object(c,'ROOT',root),patch.object(c.subprocess,'run') as run,self.assertRaises(ValueError):c.main()
   run.assert_not_called();self.assertEqual(json.loads((root/'work/evidence/b006-continuation.json').read_text())['state'],'failed')
 def test_changed_audit_never_programs(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);self.setup_root(root,'running')
   def advance(_):
    (root/'work/evidence/b005-connected-campaign.json').write_text('{"state":"completed"}')
    (root/'work/evidence/custom-build-audit-guarded06.json').write_text('{"changed":true}')
   with patch.object(c,'ROOT',root),patch.object(c.time,'sleep',advance),patch.object(c.subprocess,'run') as run,self.assertRaises(ValueError):c.main()
   run.assert_not_called()
 def test_existing_evidence_preserved(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);self.setup_root(root,'failed');p=root/'work/evidence/b006-continuation.json';p.write_text('preserve')
   with patch.object(c,'ROOT',root),self.assertRaises(ValueError):c.main()
   self.assertEqual(p.read_text(),'preserve')
 def test_ready(self):
  words=[0x53445706,0xc0000100]+[0]*14
  self.assertEqual(c.fresh_ready('SDW6 summary words='+','.join(f'{w:08x}' for w in words))['commands'],0)
 def test_nonfresh_refused(self):
  for index,value in ((1,0xc0041200),(3,1),(4,1),(0,0x53445705)):
   words=[0x53445706,0xc0000100]+[0]*14;words[index]=value
   with self.assertRaises(ValueError):c.fresh_ready('SDW6 summary words='+','.join(f'{w:08x}' for w in words))
if __name__=='__main__':unittest.main()
