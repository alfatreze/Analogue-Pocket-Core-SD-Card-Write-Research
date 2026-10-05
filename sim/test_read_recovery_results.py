#!/usr/bin/env python3
"""Verify the read-only evidence collector with temporary card trees."""
import contextlib,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import read_recovery_results as collector
import recovery
class CollectorTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'project';self.card=Path(self.temp.name)/'card';self.card.mkdir();self.root.mkdir()
  self.patches=[patch.object(collector,'ROOT',self.root),patch.object(collector.install,'CARD',self.card),patch.object(collector.install,'identity',return_value={})]
  for p in self.patches:p.start()
  for asset,gen in zip(collector.ASSETS,(63,64)):
   data=bytearray([165]*8192);data[512:1024]=recovery.record(gen);p=self.card/asset;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  (self.card/'protected.bin').write_bytes(b'protected');self.baseline=collector.install.snapshot();self.save(self.root/'work/evidence/update-recovery05/after.json',self.baseline)
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.temp.cleanup()
 def save(self,path,data):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data))
 def run_collector(self,*extra):
  with patch.object(sys,'argv',['collector','--test-id','RECOVERY-TEST','--firmware','2.7','--generation','64','--generated',*extra]),contextlib.redirect_stdout(io.StringIO()):return collector.main()
 def test_exact_generated_files(self):self.assertEqual(self.run_collector(),0)
 def test_read_only_unchanged(self):
  self.save(self.root/'work/evidence/runs/PRIOR/after.json',self.baseline);self.assertEqual(self.run_collector('--read-only-baseline','PRIOR'),0)
 def test_read_only_changed_record(self):
  self.save(self.root/'work/evidence/runs/PRIOR/after.json',self.baseline);p=self.card/collector.ASSETS[0];data=bytearray(p.read_bytes());data[512:1024]=recovery.record(62);p.write_bytes(data);self.assertEqual(self.run_collector('--read-only-baseline','PRIOR'),1)
 def test_unrelated_change(self):
  (self.card/'protected.bin').write_bytes(b'changed');self.assertEqual(self.run_collector(),1)
 def test_guard_corruption(self):
  p=self.card/collector.ASSETS[0];data=bytearray(p.read_bytes());data[0]=0;p.write_bytes(data);self.assertEqual(self.run_collector(),1)
 def test_clean_requires_both_generations(self):
  p=self.card/collector.ASSETS[0];data=bytearray(p.read_bytes());data[512:1024]=bytes([165])*512;p.write_bytes(data)
  self.assertEqual(self.run_collector('--generation-a','63','--generation-b','64'),1)
 def test_expected_pair(self):self.assertEqual(self.run_collector('--generation-a','63','--generation-b','64'),0)
 def test_existing_evidence_refused(self):
  self.run_collector()
  with self.assertRaises(ValueError):self.run_collector()
 def test_invalid_id(self):
  with self.assertRaises(ValueError):collector.test_id('../escape')
if __name__=='__main__':unittest.main()
