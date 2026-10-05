#!/usr/bin/env python3
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import jtag_load_guarded as load
class LoadTests(unittest.TestCase):
 def test_existing_ABI_matches(self):
  self.assertTrue(load.compatibility()['unchanged_slot_and_framework_ABI'])
 def test_changed_slots_refused(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   for build in ('recovery05','guarded06'):
    folder=root/'work/packages'/build/'Cores/alfatreze.CARDWRITE02';folder.mkdir(parents=True)
    (folder/'data.json').write_text(json.dumps({'changed':build}))
   with patch.object(load,'ROOT',root),self.assertRaises(ValueError):load.compatibility()
 def test_foreign_packet_refused(self):
  raw='SDW5 summary words=53445705,c0041200,0,0,2,3,3f,0,40,0,40,0,80000006,c48a0907,c48a0907,d1ae1'
  with self.assertRaises(ValueError):load.live_summary(raw,load.jtag_guarded)
 def test_absent_snapshot_refused(self):
  with self.assertRaises(ValueError):load.live_summary('console banner only',load.jtag_guarded)
 def test_safe_pauses(self):
  for point in range(4):
   words=[0x53445706,0x20080e00,0,0,2+point,3,63,0,64,0,0,0,0,0,0,1]
   raw='SDW6 summary words='+','.join(f'{w:08x}' for w in words)
   self.assertEqual(load.allowed_pause(raw,point)['commands'],2+point)
 def test_busy_or_wrong_pause_refused(self):
  base=[0x53445706,0x20080e00,0,0,3,3,63,0,64,0,0,0,0,0,0,1]
  for index,value in ((1,0x20080d00),(1,0x60080e00),(1,0x20080e01),(3,1),(4,4),(0,0x53445705)):
   words=base.copy();words[index]=value
   with self.assertRaises(ValueError):load.allowed_pause('SDW6 summary words='+','.join(f'{w:08x}' for w in words),1)
if __name__=='__main__':unittest.main()
