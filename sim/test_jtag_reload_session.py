#!/usr/bin/env python3
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import jtag_reload_session as reload
class ReloadTests(unittest.TestCase):
 def raw(self,status=4,state=18,mode=0,commands=322,completed=64):
  h=0x80000000|(0 if status==8 else 0x40000000)|(mode<<28)|(status<<16)|(state<<8)
  words=[0x53445705,h,0,completed,commands,3,63,0,64,0,1,0,0x80000007,0,0,1]
  return 'SDW5 summary words='+','.join(f'{w:08x}' for w in words)
 def test_matching_preserved_pass(self):
  raw=self.raw();_,s=reload.packet(raw);self.assertEqual(reload.allowed_snapshot(raw,{'pass':True,'summary':s}),s)
 def test_missing_history(self):
  with self.assertRaises(ValueError):reload.allowed_snapshot(self.raw())
 def test_changed_live_summary(self):
  _,s=reload.packet(self.raw());s['commands']=321
  with self.assertRaises(ValueError):reload.allowed_snapshot(self.raw(),{'pass':True,'summary':s})
 def test_busy_or_timeout_refused(self):
  for status,state in ((2,4),(7,19),(0,1)):
   raw=self.raw(status,state);_,s=reload.packet(raw)
   with self.assertRaises(ValueError):reload.allowed_snapshot(raw,{'pass':True,'summary':s})
 def test_all_safe_pause_points(self):
  for point in range(4):reload.allowed_snapshot(self.raw(8,14,2,2+point,0),point=point)
 def test_wrong_pause_or_busy_refused(self):
  for status,state,commands in ((8,14,9),(8,4,3),(2,4,3)):
   with self.assertRaises(ValueError):reload.allowed_snapshot(self.raw(status,state,2,commands,0),point=1)
if __name__=='__main__':unittest.main()
