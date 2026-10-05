#!/usr/bin/env python3
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import cleanup_research_cores as cleanup
class CleanupTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)/'project';self.card=Path(self.temp.name)/'card';self.card.mkdir();self.root.mkdir()
  self.patches=[patch.object(cleanup,'ROOT',self.root),patch.object(cleanup,'CARD',self.card),patch.object(cleanup,'EVIDENCE',self.root/'work/evidence/cleanup-b005'),patch.object(cleanup.install,'CARD',self.card),patch.object(cleanup.install,'identity',return_value={})]
  for p in self.patches:p.start()
  for name in (*cleanup.OLD,'alfatreze.CARDWRITE02','unrelated.Core'):
   p=self.card/'Cores'/name/'core.json';p.parent.mkdir(parents=True);p.write_bytes(name.encode())
  (self.card/'result.bin').write_bytes(b'actual result')
  self.baseline=cleanup.install.snapshot();p=self.root/'work/evidence/update-recovery05/after.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(self.baseline))
  p=self.root/'work/packages/recovery05-manifest.json';p.parent.mkdir(parents=True);p.write_text(json.dumps({'files':{'Cores/alfatreze.CARDWRITE02/core.json':self.baseline['Cores/alfatreze.CARDWRITE02/core.json']['sha256']}}))
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.temp.cleanup()
 def test_cleanup_and_backups(self):
  cleanup.apply(cleanup.plan())
  for old in cleanup.OLD:
   self.assertFalse((self.card/'Cores'/old).exists());self.assertEqual((cleanup.EVIDENCE/'backup/Cores'/old/'core.json').read_bytes(),old.encode())
  self.assertTrue((self.card/'Cores/unrelated.Core/core.json').exists());self.assertTrue((self.card/'Cores/alfatreze.CARDWRITE02/core.json').exists());self.assertEqual((self.card/'result.bin').read_bytes(),b'actual result')
 def test_changed_card_refused(self):
  (self.card/'result.bin').write_bytes(b'changed')
  with self.assertRaises(ValueError):cleanup.plan()
 def test_changed_plan_refused(self):
  plan=cleanup.plan();(self.card/'unexpected.bin').write_bytes(b'new')
  with self.assertRaises(ValueError):cleanup.apply(plan)
 def test_b005_mismatch_refused(self):
  p=self.root/'work/packages/recovery05-manifest.json';p.write_text(json.dumps({'files':{'Cores/alfatreze.CARDWRITE02/core.json':'bad'}}))
  with self.assertRaises(ValueError):cleanup.plan()
 def test_evidence_overwrite_refused(self):
  plan=cleanup.plan();cleanup.EVIDENCE.mkdir(parents=True);(cleanup.EVIDENCE/'journal.json').write_text('{}')
  with self.assertRaises(ValueError):cleanup.apply(plan)
if __name__=='__main__':unittest.main()
