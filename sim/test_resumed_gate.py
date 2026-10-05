#!/usr/bin/env python3
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import jtag_load_resumed as load,resume_recovery as resume
class GateTests(unittest.TestCase):
 def test_incomplete_resume_refused(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'trial.json';p.write_text('{"state":"running"}')
   with self.assertRaises(ValueError):resume.verify(p)
 def test_failed_resume_refused(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'trial.json';p.write_text('{"state":"failed","error":"transport"}')
   with self.assertRaises(ValueError):resume.verify(p)
 def test_wrong_sequence_refused(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'trial.json';p.write_text('{"state":"completed","error":null,"base":{"anchor":1},"events":[]}')
   with patch.object(resume,'base',return_value=([bytearray(8192),bytearray(8192)],{'anchor':1})),self.assertRaises(ValueError):resume.verify(p)
 def test_wrong_baseline_refused(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'trial.json';p.write_text('{"state":"completed","error":null,"base":{"anchor":2},"events":[]}')
   with patch.object(resume,'base',return_value=([bytearray(8192),bytearray(8192)],{'anchor':1})),self.assertRaises(ValueError):resume.verify(p)
 def test_proof_failure_propagates(self):
  with patch.object(load.resume_recovery,'verify',side_effect=ValueError('base differs')),self.assertRaises(ValueError):load.resumed_gate()
 def test_false_proof_refused(self):
  with patch.object(load.resume_recovery,'verify',return_value={'pass':False}),self.assertRaises(ValueError):load.resumed_gate()
 def test_matching_published_proof(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);p=root/'work/evidence/b005-resumed-summary.json';p.parent.mkdir(parents=True);p.write_text('{"pass":true,"generation":649}')
   with patch.object(load,'ROOT',root),patch.object(load.resume_recovery,'verify',return_value={'pass':True,'generation':649}):self.assertEqual(load.resumed_gate(),load.sha(p))
 def test_changed_published_proof_refused(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);p=root/'work/evidence/b005-resumed-summary.json';p.parent.mkdir(parents=True);p.write_text('{"pass":true,"generation":650}')
   with patch.object(load,'ROOT',root),patch.object(load.resume_recovery,'verify',return_value={'pass':True,'generation':649}),self.assertRaises(ValueError):load.resumed_gate()
if __name__=='__main__':unittest.main()
